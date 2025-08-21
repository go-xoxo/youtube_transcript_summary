# YouTube Transcript Summary

A robust tool for fetching YouTube video transcripts and generating AI-powered summaries using OpenAI's GPT models.

## Features

- **Robust transcript fetching** with multiple fallback methods
- **AI-powered summarization** using OpenAI GPT models
- **Sponsor/ad content filtering** to improve summary quality
- **Multiple transcript type support** (manual vs. generated)
- **Multi-language support** for transcript fetching
- **Comprehensive logging** for debugging and monitoring
- **Error resilience** with graceful failure handling

## Setup

1. Clone the repository and run the setup script:
   ```bash
   ./setup.sh
   ```

2. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

3. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Fetch Transcript

Basic usage:
```bash
python fetch_transcript.py --video_id VIDEO_ID --output transcript.txt
```

Advanced options:
```bash
python fetch_transcript.py \
  --video_id VIDEO_ID \
  --output transcript.txt \
  --transcript_type manual \
  --language en \
  --filter_sponsors
```

#### Options:
- `--video_id`: YouTube video ID (required)
- `--output`: Output file path (required)
- `--transcript_type`: Prefer `manual`, `generated`, or accept `any` (default: any)
- `--language`: Preferred language code (default: en)
- `--filter_sponsors`: Filter out sponsor/ad content from transcript
- `--source_type`: Source type - currently only `youtube` is supported

### Generate Summary

```bash
python youtube_summary.py \
  --input transcript.txt \
  --output summary.md \
  --video_id VIDEO_ID
```

#### Options:
- `--input`: Path to transcript file (required)
- `--output`: Path to output markdown file (required)
- `--video_id`: YouTube video ID for context (required)

## Transcript Content Pitfalls

### Common Issues with YouTube Transcripts

1. **Sponsor/Advertisement Content**
   - Many YouTube videos contain sponsored segments that may not be relevant to the main content
   - Use `--filter_sponsors` flag with `fetch_transcript.py` to automatically remove common sponsor patterns
   - The tool detects patterns like "sponsored by", "promo code", "get X% off", etc.

2. **Auto-Generated vs. Manual Transcripts**
   - **Auto-generated**: May contain errors, especially with technical terms, names, or accented speech
   - **Manual**: Generally more accurate but not always available
   - Use `--transcript_type manual` to prefer human-created transcripts when available

3. **Language and Localization**
   - Videos may have transcripts in multiple languages
   - Auto-translated transcripts may have lower quality than native language transcripts
   - Specify `--language` to get transcripts in your preferred language

4. **Missing Transcripts**
   - Some videos don't have transcripts (disabled by creator or unavailable)
   - Private/unlisted videos may not have accessible transcripts
   - Live streams might not have transcript data

5. **Formatting Issues**
   - Transcripts don't include punctuation in auto-generated versions
   - Speaker identification is usually not available
   - Timestamps are included but may not align perfectly with audio

### Best Practices

- Always check the transcript quality before generating summaries
- For important content, manually review auto-generated transcripts
- Consider the video's audio quality when evaluating transcript accuracy
- Use sponsor filtering for educational or informational content

## Testing

Run the included test scripts to verify functionality:

```bash
# Test transcript fetching
python test_fetch_transcript.py

# Test summary generation  
python test_youtube_summary.py
```

### Test Coverage

The test scripts cover:
- **Command-line argument validation**
- **Error handling for missing files and invalid inputs**
- **API key validation**
- **Directory creation for output files**
- **Sponsor content detection**
- **Transcript type preferences**
- **Language preferences**

### Test Limitations

- Tests run without network access, so actual transcript fetching is not tested
- OpenAI API calls are tested with fake keys to verify error handling
- Network-dependent features are tested up to the point of external API calls

## Error Handling

The tools include comprehensive error handling for:

- **Network connectivity issues**
- **Missing or invalid video IDs**
- **Unavailable transcripts**
- **API rate limiting and errors**
- **File I/O problems**
- **Missing dependencies**

All errors are logged with appropriate detail levels and user-friendly error messages.

## Environment Variables

- `OPENAI_API_KEY`: Required for summary generation
- Set logging level with standard Python logging environment variables

## Dependencies

See `requirements.txt` for a full list of Python dependencies. Key libraries include:

- `youtube-transcript-api`: Primary transcript fetching
- `pytube`: Fallback transcript method
- `pafy`: Video metadata fetching
- `openai`: AI-powered summarization
- `pathlib`: File path handling

## Troubleshooting

### Common Issues

1. **"No transcript found"**: Video may not have transcripts enabled
2. **"API key not found"**: Set the `OPENAI_API_KEY` environment variable
3. **Network errors**: Check internet connectivity and YouTube accessibility
4. **Pafy backend errors**: These are usually non-fatal and fallback methods will be used

### Logging

Both scripts provide detailed logging output. Increase verbosity by modifying the logging level in the script files.

## Contributing

When contributing:
1. Run the test scripts to ensure functionality
2. Add appropriate logging for new features
3. Handle errors gracefully with user-friendly messages
4. Update documentation for new options or features

## License

[Specify your license here]