import os
import argparse
import logging
import re
from pathlib import Path
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, required=True, help='Path to transcript file')
parser.add_argument('--output', type=str, required=True, help='Path to output markdown file')
parser.add_argument('--video_id', type=str, required=True, help='YouTube video ID')
args = parser.parse_args()

# Check for OpenAI API key
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    logger.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    print("ERROR: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    exit(1)

logger.info(f"Reading transcript from: {args.input}")

try:
    with open(args.input, 'r', encoding='utf-8', errors='replace') as f:
        transcript = f.read()
except FileNotFoundError:
    logger.error(f"Transcript file not found: {args.input}")
    print(f"ERROR: Transcript file not found: {args.input}")
    exit(1)
except Exception as e:
    logger.error(f"Failed to read transcript file: {e}")
    print(f"ERROR: Failed to read transcript file: {e}")
    exit(1)

# Check for sponsor/ad content patterns
sponsor_patterns = [
    r'sponsored by',
    r'this video is sponsored',
    r'thanks to.*for sponsoring',
    r'our sponsor',
    r'get \d+% off',
    r'promo code',
    r'affiliate link',
    r'ground\.? ?news',
    r'skillshare',
    r'nordvpn',
    r'brilliant\.org'
]

transcript_lower = transcript.lower()
sponsor_found = any(re.search(pattern, transcript_lower) for pattern in sponsor_patterns)

if sponsor_found:
    logger.warning("Sponsor/ad content detected in transcript. Summary may include promotional content.")
    print("WARNING: Sponsor/ad content detected in transcript. Summary may include promotional content.")

# Ensure output directory exists
output_path = Path(args.output)
output_path.parent.mkdir(parents=True, exist_ok=True)

logger.info("Generating summary using OpenAI...")

try:
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "You are a helpful assistant. Summarize the following YouTube transcript in markdown with a lot of emojis. Start with a title that includes the video ID."
            },
            {
                "role": "user", 
                "content": f"Video ID: {args.video_id}\n\nTranscript:\n{transcript}"
            }
        ],
        max_tokens=3000
    )
    
    summary = response.choices[0].message.content
    logger.info("Summary generated successfully")
    
except Exception as e:
    logger.error(f"Failed to generate summary: {e}")
    print(f"ERROR: Failed to generate summary: {e}")
    exit(1)

logger.info(f"Writing summary to: {args.output}")

try:
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(summary)
    logger.info("Summary written successfully")
    print(f"Summary saved to: {args.output}")
except Exception as e:
    logger.error(f"Failed to write summary file: {e}")
    print(f"ERROR: Failed to write summary file: {e}")
    exit(1)
