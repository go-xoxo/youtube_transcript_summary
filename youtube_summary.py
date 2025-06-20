import os
import argparse
from openai import OpenAI

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, required=True, help='Path to transcript file')
parser.add_argument('--output', type=str, required=True, help='Path to output markdown file')
parser.add_argument('--video_id', type=str, required=True, help='YouTube video ID')
args = parser.parse_args()

with open(args.input, 'r', encoding='utf-8', errors='replace') as f:
    transcript = f.read()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

response = client.responses.create(
    model="gpt-4.1-mini",
    instructions=f"You are a helpful assistant. Summarize the following YouTube transcript in markdown with a lot of emojis. Start with a title that includes the video ID ({args.video_id}).",
    input=transcript,
    max_output_tokens=3000  # You can adjust this as needed
)

with open(args.output, 'w', encoding='utf-8') as f:
    f.write(response.output_text)
