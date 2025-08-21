import argparse
import logging
import os
import re
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from xml.etree.ElementTree import ParseError
import pafy
from pytube import YouTube

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Fix for pafy: Use youtube_dl backend ---
def setup_pafy_backend():
    """Setup pafy backend with proper error handling."""
    try:
        import pafy
        pafy.backend_shared.backend = "internal"
        logger.info("Pafy backend set to 'internal'")
        return True
    except Exception as e:
        logger.warning(f"Failed to set pafy backend: {e}")
        try:
            import pafy
            pafy.set_api_key(None)  # Fallback
            logger.info("Pafy fallback setup completed")
            return True
        except Exception as e2:
            logger.error(f"Pafy setup failed completely: {e2}")
            return False

setup_pafy_backend()

parser = argparse.ArgumentParser(description="Fetch YouTube transcript with robustness features")
parser.add_argument("--video_id", required=True, help="YouTube video ID")
parser.add_argument("--output", required=True, help="Output file path")
parser.add_argument("--transcript_type", choices=["manual", "generated", "any"], default="any", 
                    help="Prefer manual, generated, or accept any transcript type")
parser.add_argument("--language", default="en", help="Preferred language code (default: en)")
parser.add_argument("--filter_sponsors", action="store_true", default=False,
                    help="Filter out sponsor/ad content from transcript")
parser.add_argument("--source_type", choices=["youtube", "other"], default="youtube",
                    help="Source type (youtube or other)")
args = parser.parse_args()

video_id = args.video_id
output_path = args.output

logger.info(f"Fetching transcript for video: {video_id}")
logger.info(f"Output path: {output_path}")
logger.info(f"Transcript type preference: {args.transcript_type}")
logger.info(f"Language preference: {args.language}")

# Ensure output directory exists
output_dir = Path(output_path).parent
output_dir.mkdir(parents=True, exist_ok=True)
logger.info(f"Output directory ensured: {output_dir}")

# Handle non-YouTube sources
if args.source_type != "youtube":
    logger.warning("Non-YouTube sources not yet implemented")
    error_msg = "Non-YouTube sources are not yet supported. This is a placeholder for future functionality."
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"ERROR: {error_msg}\n")
        logger.error(error_msg)
    except Exception as e:
        logger.error(f"Failed to write error message to output file: {e}")
    exit(1)

# --- Fetch metadata ---
metadata_str = ""
try:
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.info(f"Fetching metadata for: {video_url}")
    video = pafy.new(video_url)

    logger.info("Video Metadata:")
    logger.info(f"Title: {video.title}")
    logger.info(f"Author: {video.author}")
    logger.info(f"Duration: {video.duration}")
    logger.info(f"Views: {video.viewcount}")
    logger.info(f"Description: {video.description[:300]}...")

    metadata_str = f"""Title: {video.title}
Author: {video.author}
Duration: {video.duration}
Views: {video.viewcount}
Description: {video.description}
"""
except Exception as e:
    logger.warning(f"Failed to fetch metadata: {e}")
    metadata_str = "[WARN] Metadata not available.\n"

def filter_sponsor_content(text):
    """Filter out sponsor/ad content from transcript."""
    if not args.filter_sponsors:
        return text
    
    logger.info("Filtering sponsor/ad content...")
    
    # Common sponsor/ad patterns to remove
    sponsor_patterns = [
        r'this video is sponsored by.*?(?=\n|$)',
        r'thanks to.*?for sponsoring.*?(?=\n|$)',
        r'our sponsor.*?(?=\n|$)',
        r'get \d+%? off.*?(?=\n|$)',
        r'use promo code.*?(?=\n|$)',
        r'visit.*?\.com.*?(?=\n|$)',
        r'link in description.*?(?=\n|$)',
        # Ground News specific (from the example transcript)
        r'ground\.? ?news.*?(?=back to|now back|so now|$)',
        # General sponsor transition phrases
        r'but first.*?sponsor.*?(?=back to|now back|so now|$)',
        r'but before we.*?sponsor.*?(?=back to|now back|so now|$)',
    ]
    
    filtered_text = text
    removed_sections = []
    
    for pattern in sponsor_patterns:
        matches = re.findall(pattern, filtered_text, re.IGNORECASE | re.DOTALL)
        if matches:
            removed_sections.extend(matches)
            filtered_text = re.sub(pattern, '', filtered_text, flags=re.IGNORECASE | re.DOTALL)
    
    if removed_sections:
        logger.info(f"Removed {len(removed_sections)} sponsor/ad sections")
        for section in removed_sections[:3]:  # Log first 3 for debugging
            logger.debug(f"Removed section: {section[:100]}...")
    
    # Clean up extra whitespace
    filtered_text = re.sub(r'\n\s*\n\s*\n', '\n\n', filtered_text)
    
    return filtered_text

def select_best_transcript(transcript_list, preference_type, language):
    """Select the best transcript based on user preferences."""
    logger.info(f"Available transcripts:")
    available_transcripts = []
    
    for t in transcript_list:
        t_type = "generated" if t.is_generated else "manual"
        logger.info(f"  - {t.language_code} ({t_type})")
        available_transcripts.append((t, t_type))
    
    # First, try to find transcripts in the preferred language
    lang_matches = [t for t, _ in available_transcripts if t.language_code.startswith(language)]
    
    if not lang_matches:
        logger.warning(f"No transcripts found for language '{language}', trying all available")
        lang_matches = [t for t, _ in available_transcripts]
    
    if not lang_matches:
        raise NoTranscriptFound(f"No transcripts available for video {video_id}")
    
    # Apply transcript type preference
    if preference_type == "manual":
        manual_transcripts = [t for t in lang_matches if not t.is_generated]
        if manual_transcripts:
            selected = manual_transcripts[0]
            logger.info(f"Selected manual transcript: {selected.language_code}")
            return selected
        logger.warning("No manual transcripts found, falling back to generated")
    elif preference_type == "generated":
        generated_transcripts = [t for t in lang_matches if t.is_generated]
        if generated_transcripts:
            selected = generated_transcripts[0]
            logger.info(f"Selected generated transcript: {selected.language_code}")
            return selected
        logger.warning("No generated transcripts found, falling back to manual")
    
    # Default: select first available
    selected = lang_matches[0]
    t_type = "generated" if selected.is_generated else "manual"
    logger.info(f"Selected transcript: {selected.language_code} ({t_type})")
    return selected

# --- Fetch transcript ---
try:
    logger.info("Fetching transcript using YouTubeTranscriptApi...")
    transcript_list = YouTubeTranscriptApi().list(video_id)
    
    transcript = select_best_transcript(transcript_list, args.transcript_type, args.language)

    try:
        logger.info("Fetching transcript content...")
        fetched = transcript.fetch()
    except ParseError:
        logger.warning("Broken XML detected. Trying to translate transcript...")
        if transcript.is_translatable:
            try:
                logger.info(f"Translating transcript to {args.language}...")
                transcript = transcript.translate(args.language)
                fetched = transcript.fetch()
            except Exception as e:
                logger.error(f"Failed to fetch translated transcript: {e}")
                raise e
        else:
            logger.error("Transcript is not translatable and has broken XML")
            raise

    if fetched is None:
        raise ValueError("Transcript object is None or broken.")

    logger.info(f"Successfully fetched {len(fetched)} transcript segments")
    text = "\n".join([snippet.text for snippet in fetched])
    
    # Apply sponsor filtering if requested
    if args.filter_sponsors:
        text = filter_sponsor_content(text)
    
    logger.info(f"Writing transcript to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(metadata_str + "\n" + text)
    
    logger.info("Transcript saved successfully")

except (NoTranscriptFound, TranscriptsDisabled) as e:
    logger.error(f"No transcript found: {e}")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("TRANSCRIPT_NOT_FOUND")
        logger.info("Wrote 'TRANSCRIPT_NOT_FOUND' to output file")
    except Exception as write_e:
        logger.error(f"Failed to write error message to output file: {write_e}")

except Exception as e:
    logger.warning(f"YouTubeTranscriptApi failed: {e}. Trying pytube fallback...")
    try:
        logger.info("Using pytube fallback...")
        yt = YouTube(video_url)
        # select English captions (manual or auto)
        caption = (
            yt.captions.get_by_language_code(args.language)
            or yt.captions.get_by_language_code(f'a.{args.language}')
            or yt.captions.get_by_language_code(f'{args.language}-US')
            or yt.captions.get_by_language_code(f'{args.language}-GB')
            # `yt.captions` behaves like a dict where iterating yields language
            # codes. Previously we tried `next(iter(yt.captions), None)` which
            # returned a language code string. Attempting to call
            # `generate_srt_captions()` on that string would raise an
            # AttributeError. Instead, iterate over the values to get an actual
            # Caption object.
            or next(iter(yt.captions.values()), None)
        )
        if not caption:
            raise ValueError('No captions available via pytube')
        
        logger.info("Generating SRT captions...")
        srt_captions = caption.generate_srt_captions()
        lines = []
        for line in srt_captions.splitlines():
            if line.strip().isdigit() or '-->' in line:
                continue
            lines.append(line)
        text = "\n".join(lines)
        
        # Apply sponsor filtering if requested
        if args.filter_sponsors:
            text = filter_sponsor_content(text)
        
        logger.info(f"Writing pytube transcript to: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(metadata_str + "\n" + text)
        
        logger.info("Pytube transcript saved successfully")
        
    except Exception as e2:
        logger.error(f"Pytube fallback failed: {e2}")
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("TRANSCRIPT_NOT_FOUND")
            logger.info("Wrote 'TRANSCRIPT_NOT_FOUND' to output file after all methods failed")
        except Exception as write_e:
            logger.error(f"Failed to write error message to output file: {write_e}")
