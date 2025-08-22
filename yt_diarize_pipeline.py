#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yt_diarize_pipeline.py
End-to-end: YouTube video_id -> diarized transcript (AssemblyAI) -> deduped, merged transcript + SRT
"""

import os
import sys
import json
import time
import string
import difflib
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List

import requests
from tqdm import tqdm

# ---------------- Config ----------------
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks
POLL_BASE_DELAY = 2.0
POLL_MAX_DELAY = 10.0
SRT_CHARS_PER_CAPTION = 40
YT_AUDIO_FORMAT = "bestaudio/best"
OUTPUT_DIR = Path("outputs")
# ----------------------------------------

API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not API_KEY:
    print("[ERROR] ASSEMBLYAI_API_KEY not set.", file=sys.stderr)
    sys.exit(1)

AAI_BASE = os.getenv("ASSEMBLYAI_BASE", "https://api.assemblyai.com")
API_UPLOAD = f"{AAI_BASE}/v2/upload"
API_TRANSCRIPT = f"{AAI_BASE}/v2/transcript"

HEADERS_JSON = {"authorization": API_KEY, "content-type": "application/json"}
HEADERS_UPLOAD = {"authorization": API_KEY}


# ---------- Helpers ----------
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
    t = t.strip().replace("…", " ").replace("—", " ")
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
        start, end, text = (
            u.get("start", 0),
            u.get("end", 0),
            normalize_line(u.get("text", "")),
        )
        if not text:
            continue
        if merged and near_duplicate(text, last_text):
            continue
        if merged:
            prev = merged[-1]
            if prev["speaker"] == spk and start - prev["end"] <= max_gap_ms:
                prev["text"] = (prev["text"] + " " + text).strip()
                prev["end"] = max(prev["end"], end)
                last_text = prev["text"]
                continue
        merged.append({"speaker": spk, "start": start, "end": end, "text": text})
        last_text = text
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


# ---------- AssemblyAI ----------
def upload_file(file_path: Path) -> str:
    size = file_path.stat().st_size
    with (
        file_path.open("rb") as f,
        tqdm(total=size, unit="B", unit_scale=True, desc="Upload") as pbar,
    ):

        def gen() -> Iterable[bytes]:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                pbar.update(len(chunk))
                yield chunk

        resp = requests.post(API_UPLOAD, headers=HEADERS_UPLOAD, data=gen())
    resp.raise_for_status()
    return resp.json()["upload_url"]


def request_transcript(audio_url: str) -> str:
    payload = {
        "audio_url": audio_url,
        "speaker_labels": True,
        "punctuate": True,
        "format_text": True,
    }
    r = requests.post(API_TRANSCRIPT, headers=HEADERS_JSON, json=payload)
    r.raise_for_status()
    return r.json()["id"]


def poll_transcript(tid: str) -> Dict:
    url = f"{API_TRANSCRIPT}/{tid}"
    delay = POLL_BASE_DELAY
    while True:
        r = requests.get(url, headers=HEADERS_JSON)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "completed":
            return data
        if data.get("status") == "error":
            raise RuntimeError(data.get("error"))
        time.sleep(delay)
        delay = min(POLL_MAX_DELAY, delay * 1.3)


# ---------- yt-dlp ----------
def download_audio(video_id: str, workdir: Path) -> Path:
    out = workdir / f"{video_id}.%(ext)s"
    cmd = [
        "yt-dlp",
        "-f",
        YT_AUDIO_FORMAT,
        "-x",
        "--audio-format",
        "m4a",
        "-o",
        str(out),
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    subprocess.run(cmd, check=True)
    for p in workdir.glob(f"{video_id}.*"):
        if p.suffix.lower() in (".m4a", ".webm", ".mp3", ".opus"):
            return p
    raise FileNotFoundError("No audio file.")


# ---------- Main ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python yt_diarize_pipeline.py <video_id>")
        sys.exit(2)
    video_id = sys.argv[1].strip()
    out_dir = OUTPUT_DIR / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        audio_path = download_audio(video_id, Path(td))
        upload_url = upload_file(audio_path)

    tid = request_transcript(upload_url)
    data = poll_transcript(tid)
    utterances = data.get("utterances", [])
    if not utterances:
        utterances = [
            {
                "speaker": "Speaker 1",
                "start": 0,
                "end": data.get("audio_duration", 0) * 1000,
                "text": data.get("text", ""),
            }
        ]

    merged = merge_utterances(utterances)
    write_json(
        {"video_id": video_id, "utterances": merged}, out_dir / "transcript.json"
    )
    write_txt(merged, out_dir / "transcript.txt")
    write_srt(merged, out_dir / "captions.srt")

    print(f"[OK] Outputs saved in {out_dir}")


if __name__ == "__main__":
    main()
