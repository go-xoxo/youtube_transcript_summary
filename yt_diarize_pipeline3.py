#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yt_diarize_pipeline.py
YouTube video_id -> diarized transcript (AssemblyAI) -> merged, redundancy-free transcript + SRT
Optimized for speed: aria2c multi-connection downloads, optional low-bitrate audio, larger upload chunks.

Env:
  ASSEMBLYAI_API_KEY  (required)
  ASSEMBLYAI_BASE     (optional, e.g. https://api.eu.assemblyai.com)

CLI:
  python yt_diarize_pipeline.py <video_id>
    [--fast]                   # smaller audio (Opus 64 kbps) to speed upload
    [--chunk-size-mb 32]       # HTTP upload chunk size
    [--log-level INFO|DEBUG|WARNING|ERROR]
    [--no-srt]                 # skip SRT generation
"""

import argparse
import json
import os
import string
import sys
import time
import difflib
import tempfile
import subprocess
import shutil
import traceback
from pathlib import Path
from typing import Dict, Iterable, List

import requests
from tqdm import tqdm
import logging
from logging import Handler, LogRecord

# ---------------- Defaults ----------------
DEFAULT_CHUNK_MB = 32  # Bigger chunks reduce HTTP overhead
POLL_BASE_DELAY = 2.0
POLL_MAX_DELAY = 10.0
YT_AUDIO_FORMAT = "bestaudio/best"
OUTPUT_DIR = Path("outputs")
# ------------------------------------------


# ---------- Logging (tqdm-friendly) ----------
class TqdmHandler(Handler):
    def emit(self, record: LogRecord) -> None:
        try:
            tqdm.write(self.format(record))
        except Exception:
            sys.stderr.write(self.format(record) + "\n")


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not any(isinstance(h, TqdmHandler) for h in logger.handlers):
        h = TqdmHandler()
        fmt = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger


log = get_logger("yt_diarize", logging.DEBUG)


# ---------- Utilities ----------
def secs_to_hms(ms: int) -> str:
    s = ms / 1000.0
    h = int(s // 3600)
    s -= h * 3600
    m = int(s // 60)
    s -= m * 60
    return f"{h:02d}:{m:02d}:{int(s):02d}"


def srt_timestamp(ms: int) -> str:
    s = ms / 1000.0
    h = int(s // 3600)
    s -= h * 3600
    m = int(s // 60)
    s -= m * 60
    sec = int(s)
    ms_rem = int(round((s - sec) * 1000))
    return f"{h:02d}:{m:02d}:{sec:02d},{ms_rem:03d}"


def normalize_line(t: str) -> str:
    t = t.strip().replace("…", " ").replace("—", " ").replace("–", " ")
    t = " ".join(t.split())
    return t


def near_duplicate(a: str, b: str, thresh: float = 0.92) -> bool:
    if not a or not b:
        return False
    ra = normalize_line(a).lower().strip(string.punctuation)
    rb = normalize_line(b).lower().strip(string.punctuation)
    if not ra or not rb:
        return False
    return difflib.SequenceMatcher(None, ra, rb).ratio() >= thresh


def merge_utterances(utts: List[Dict], max_gap_ms: int = 1200) -> List[Dict]:
    merged, last_text = [], ""
    for u in utts:
        spk = u.get("speaker", "Speaker ?")
        start, end = int(u.get("start", 0)), int(u.get("end", 0))
        text = normalize_line(u.get("text", ""))
        if not text:
            continue
        if merged and near_duplicate(text, last_text):
            log.debug(f"Dropping near-duplicate: '{text[:80]}...'")
            continue
        if merged:
            prev = merged[-1]
            if prev["speaker"] == spk and (start - prev["end"]) <= max_gap_ms:
                prev["text"] = (prev["text"] + " " + text).strip()
                prev["end"] = max(prev["end"], end)
                last_text = prev["text"]
                continue
        merged.append({"speaker": spk, "start": start, "end": end, "text": text})
        last_text = text
    log.info(f"Merged utterances: raw={len(utts)} -> merged={len(merged)}")
    return merged


def write_txt(merged: List[Dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for u in merged:
            f.write(
                f"[{secs_to_hms(u['start'])}–{secs_to_hms(u['end'])}] {u['speaker']}: {u['text']}\n"
            )


def write_json(data: Dict, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_srt(utts: List[Dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for i, u in enumerate(utts, 1):
            f.write(
                f"{i}\n{srt_timestamp(u['start'])} --> {srt_timestamp(u['end'])}\n{u['speaker']}: {u['text']}\n\n"
            )


# ---------- AssemblyAI API helpers ----------
def get_api_info() -> Dict[str, str]:
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        log.error("ASSEMBLYAI_API_KEY not set.")
        sys.exit(1)
    base = os.getenv("ASSEMBLYAI_BASE", "https://api.assemblyai.com")
    return {
        "api_key": api_key,
        "base": base,
        "upload": f"{base}/v2/upload",
        "transcript": f"{base}/v2/transcript",
    }


def upload_file(file_path: Path, upload_url: str, api_key: str, chunk_mb: int) -> str:
    chunk_size = int(chunk_mb * 1024 * 1024)
    size = file_path.stat().st_size
    log.info(
        f"Uploading: {file_path.name} ({size / 1e6:.2f} MB) in ~{max(1, size // chunk_size)} chunks of ~{chunk_mb} MB"
    )
    headers = {"authorization": api_key}
    with (
        file_path.open("rb") as f,
        tqdm(
            total=size,
            unit="B",
            unit_scale=True,
            desc=f"Upload ({chunk_mb}MB)",
            leave=False,
        ) as pbar,
    ):

        def gen() -> Iterable[bytes]:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                pbar.update(len(chunk))
                yield chunk

        resp = requests.post(upload_url, headers=headers, data=gen(), timeout=600)
    try:
        resp.raise_for_status()
    except Exception:
        log.error("Upload failed with HTTP error.")
        log.error(resp.text)
        raise
    try:
        upload = resp.json().get("upload_url")
    except Exception:
        log.error("Failed to parse upload response as JSON.")
        log.error(resp.text)
        raise
    if not upload:
        raise RuntimeError(f"Upload response missing 'upload_url': {resp.text}")
    log.info("Upload completed.")
    return upload


def request_transcript(audio_url: str, transcript_url: str, api_key: str) -> str:
    payload = {
        "audio_url": audio_url,
        "speaker_labels": True,
        "punctuate": True,
        "format_text": True,
        "language_detection": True,
    }
    headers = {"authorization": api_key, "content-type": "application/json"}
    r = requests.post(transcript_url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    tid = r.json()["id"]
    log.info(f"Transcript requested. ID={tid}")
    return tid


def poll_transcript(tid: str, transcript_url: str, api_key: str) -> Dict:
    """
    Robust polling:
      - Retries on 5xx, timeouts, connection errors, and 429.
      - Exponential backoff with jitter.
      - Hard cap on total wait time (4h).
    """
    import random

    url = f"{transcript_url}/{tid}"
    headers = {"authorization": api_key}
    delay = POLL_BASE_DELAY  # starts at 2.0s (from config)
    max_delay = 30.0  # allow a bit more than the default 10s
    max_wait_sec = 4 * 3600  # 4 hours cap
    start_ts = time.time()

    log.info("Polling transcript status …")
    with tqdm(desc="Transcribe", unit="check", leave=False) as pbar:
        while True:
            # Hard timeout guard
            if time.time() - start_ts > max_wait_sec:
                raise TimeoutError("Polling exceeded maximum wait time (4h).")

            try:
                r = requests.get(url, headers=headers, timeout=60)
                # Treat 5xx as retryable without raising immediately
                if 500 <= r.status_code < 600:
                    tqdm.write(f"  Server {r.status_code}; retrying in {delay:.1f}s")
                    time.sleep(delay + random.uniform(0, 0.5))
                    delay = min(max_delay, delay * 1.5)
                    pbar.update(1)
                    continue

                # For other statuses, raise if error (so we can examine code)
                r.raise_for_status()
                data = r.json()

            except requests.exceptions.Timeout:
                tqdm.write(f"  Timeout; retrying in {delay:.1f}s")
                time.sleep(delay + random.uniform(0, 0.5))
                delay = min(max_delay, delay * 1.5)
                pbar.update(1)
                continue

            except requests.exceptions.ConnectionError as e:
                tqdm.write(f"  Connection error: {e}; retrying in {delay:.1f}s")
                time.sleep(delay + random.uniform(0, 0.5))
                delay = min(max_delay, delay * 1.5)
                pbar.update(1)
                continue

            except requests.exceptions.HTTPError as e:
                code = getattr(e.response, "status_code", None)
                # Retry 429 (rate limit) similar to 5xx
                if code == 429:
                    tqdm.write(f"  HTTP 429 (rate limit); retrying in {delay:.1f}s")
                    time.sleep(delay + random.uniform(0, 0.5))
                    delay = min(max_delay, delay * 1.5)
                    pbar.update(1)
                    continue
                # Non-retryable 4xx: surface the error
                raise

            # Successful JSON
            status = data.get("status")
            if status == "completed":
                log.info("Transcription completed.")
                return data
            if status == "error":
                raise RuntimeError(f"Transcription error: {data.get('error')}")

            # Still processing/queued — backoff and continue
            tqdm.write(f"  Status: {status} (retry in {delay:.1f}s)")
            time.sleep(delay + random.uniform(0, 0.5))
            delay = min(max_delay, delay * 1.3)
            pbar.update(1)


def try_download_srt(tid: str, base_url: str, api_key: str) -> str:
    url = f"{base_url}/v2/transcript/{tid}/srt"
    headers = {"authorization": api_key}
    r = requests.get(url, headers=headers, timeout=60)
    if r.status_code == 200 and r.text.strip():
        return r.text
    log.warning(f"SRT not available (status={r.status_code}); will synthesize.")
    return ""


# ---------- yt-dlp (fast) ----------
def has_aria2c() -> bool:
    return shutil.which("aria2c") is not None


def download_audio(video_id: str, workdir: Path, fast: bool) -> Path:
    """
    Download audio quickly:
      - If aria2c is available, use it with multiple connections.
      - Otherwise fall back to yt-dlp's internal downloader.
      - In --fast mode, transcode to Opus @ 64 kbps to shrink upload size.
    """
    out = workdir / f"{video_id}.%(ext)s"
    yurl = f"https://www.youtube.com/watch?v={video_id}"

    # Base command
    cmd = [
        "yt-dlp",
        "-f",
        YT_AUDIO_FORMAT,
        "-o",
        str(out),
        "--retries",
        "20",
        "--fragment-retries",
        "20",
        "--concurrent-fragments",
        "32",
        yurl,
    ]

    # Extract audio postprocessor
    if fast:
        # Smaller file = faster uploads. Opus @ 64k via postprocessor args.
        log.info("FAST mode: converting audio to Opus @ 64 kbps")
        cmd += [
            "-x",
            "--audio-format",
            "opus",
            "--postprocessor-args",
            "ffmpeg:-b:a 64k",
        ]
    else:
        cmd += ["-x", "--audio-format", "m4a"]

    # Use aria2c if present
    if has_aria2c():
        log.info("Using external downloader: aria2c (-x16 -s16 -k1M)")
        cmd += [
            "--external-downloader",
            "aria2c",
            "--external-downloader-args",
            "aria2c:-x16 -s16 -k1M",
        ]
    else:
        log.warning(
            "aria2c not found; using yt-dlp's internal downloader (still fine, just a bit slower)"
        )

    log.debug(f"yt-dlp command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Locate output
    for p in workdir.glob(f"{video_id}.*"):
        if p.suffix.lower() in (".m4a", ".webm", ".mp3", ".opus"):
            log.info(f"Audio downloaded: {p.name} ({p.stat().st_size / 1e6:.2f} MB)")
            return p
    raise FileNotFoundError("Audio file not found after yt-dlp run.")


# ---------- Main ----------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="YouTube -> diarized transcript (AssemblyAI), fast pipeline."
    )
    parser.add_argument("video_id", help="YouTube video ID (e.g., 01C3a4fL1m0)")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Shrink audio to ~64 kbps Opus to speed upload",
    )
    parser.add_argument(
        "--chunk-size-mb",
        type=int,
        default=DEFAULT_CHUNK_MB,
        help="Upload chunk size (MB)",
    )
    parser.add_argument(
        "--log-level",
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--no-srt",
        action="store_true",
        help="Do not fetch/synthesize SRT; only JSON/TXT",
    )
    args = parser.parse_args()

    # Logging level
    level = getattr(logging, args.log_level.upper(), logging.DEBUG)
    for h in log.handlers:
        h.setLevel(level)
    log.setLevel(level)
    log.debug(f"Log level: {args.log_level.upper()}")

    api = get_api_info()
    log.info(f"AssemblyAI base: {api['base']}")
    log.info(f"Upload chunk size: {args.chunk_size_mb} MB")

    video_id = args.video_id.strip()
    out_dir = OUTPUT_DIR / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"Output directory: {out_dir.resolve()}")

    try:
        # 1) Download audio quickly
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            audio_path = download_audio(video_id, tmp, fast=args.fast)

            # 2) Upload (big chunks)
            upload_url = upload_file(
                audio_path, api["upload"], api["api_key"], args.chunk_size_mb
            )

        # 3) Request diarized transcript
        tid = request_transcript(upload_url, api["transcript"], api["api_key"])

        # 4) Poll for completion
        data = poll_transcript(tid, api["transcript"], api["api_key"])

        # 5) Utterances
        utterances = data.get("utterances") or []
        if not utterances:
            log.warning(
                "No diarized utterances returned; falling back to single block from full text."
            )
            text = data.get("text", "")
            duration_ms = int(float(data.get("audio_duration", 0)) * 1000)
            utterances = [
                {"speaker": "Speaker 1", "start": 0, "end": duration_ms, "text": text}
            ]

        # Normalize labels
        for u in utterances:
            s = str(u.get("speaker", "?"))
            if not s.lower().startswith("speaker"):
                u["speaker"] = f"Speaker {s.upper()}"

        # 6) Merge & de-dup
        merged = merge_utterances(utterances)

        # 7) Write outputs
        json_path = out_dir / "transcript.json"
        txt_path = out_dir / "transcript.txt"
        write_json(
            {
                "video_id": video_id,
                "transcript_id": data.get("id"),
                "status": data.get("status"),
                "language": data.get("language_code"),
                "duration_sec": data.get("audio_duration"),
                "utterances_merged": merged,
            },
            json_path,
        )
        write_txt(merged, txt_path)
        log.info(f"Wrote JSON: {json_path}")
        log.info(f"Wrote TXT : {txt_path}")

        # 8) SRT
        if not args.no_srt:
            srt_path = out_dir / "captions.srt"
            srt_text = try_download_srt(data["id"], api["base"], api["api_key"])
            if srt_text:
                srt_path.write_text(srt_text, encoding="utf-8")
                log.info(f"Wrote SRT (API): {srt_path}")
            else:
                write_srt(merged, srt_path)
                log.info(f"Wrote SRT (synth): {srt_path}")
        else:
            log.warning("Skipping SRT per --no-srt flag.")

        log.info("All done ✅")
        return 0

    except Exception as e:
        log.error("Fatal error in pipeline:")
        log.error(str(e))
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
