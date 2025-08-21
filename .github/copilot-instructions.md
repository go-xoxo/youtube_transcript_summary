# YouTube Transcript Summary

YouTube Transcript Summary is a Python CLI tool that fetches YouTube video transcripts and generates AI-powered summaries using OpenAI. The tool includes fallback mechanisms for transcript fetching and produces markdown-formatted summaries with emojis.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

- Bootstrap and setup the repository:
  - `bash setup.sh` -- takes 23-60 seconds to complete. NEVER CANCEL. Set timeout to 120+ seconds.
  - This creates a Python virtual environment (.venv) and installs all dependencies from requirements.txt
  - May fail with network timeouts in restricted environments - document as "setup.sh fails due to network limitations"
  - `source .venv/bin/activate` -- activate the virtual environment for all subsequent commands
  - `export OPENAI_API_KEY=<your_key>` -- required for summarization functionality
  - Alternative manual setup if setup.sh fails:
    - `python3 -m venv .venv`
    - `source .venv/bin/activate`
    - `pip install --timeout=300 -r requirements.txt` -- may take up to 5 minutes with network issues

- Validate the installation:
  - `python -m py_compile fetch_transcript.py youtube_summary.py` -- compile check (instant)
  - `python test_imports.py` -- verify all dependencies import correctly (if dependencies are installed)
  - May fail if setup.sh encountered network issues

- Run transcript fetching:
  - `python fetch_transcript.py --video_id <youtube_video_id> --output <transcript_file.txt>`
  - Takes 1-30 seconds depending on video length and network connectivity
  - Requires internet access to YouTube
  - Falls back through multiple libraries: youtube-transcript-api → pytube → pafy
  - Outputs "TRANSCRIPT_NOT_FOUND" if all methods fail

- Run summary generation:
  - `python youtube_summary.py --input <transcript_file.txt> --output <summary.md> --video_id <youtube_video_id>`
  - Requires valid OPENAI_API_KEY environment variable
  - Takes 5-30 seconds depending on transcript length and OpenAI API response time
  - Uses gpt-4.1-mini model with 3000 max tokens

## Validation

- ALWAYS test both scripts after making changes:
  - Test compilation: `python -m py_compile fetch_transcript.py youtube_summary.py`
  - Test transcript fetching: `python fetch_transcript.py --video_id qSGkJ_vsuUg --output test_transcript.txt` (requires working setup)
  - Test summary generation: `python youtube_summary.py --input transcript_qSGkJ_vsuUg.txt --output test_summary.md --video_id qSGkJ_vsuUg` (requires OPENAI_API_KEY)
- ALWAYS validate that the virtual environment is activated before running Python commands
- Test with existing sample data if network/dependencies are not available:
  - Sample transcript: `transcript_qSGkJ_vsuUg.txt` (33,961 characters)
  - Test file reading: `python -c "with open('transcript_qSGkJ_vsuUg.txt', 'r') as f: print(f'Read {len(f.read())} chars')"`
- If dependencies cannot be installed due to network limitations:
  - Focus on code structure and syntax validation
  - Use static analysis and compilation checks
  - Review code logic without running full workflows
- No CI/CD pipeline exists - manual testing is required
- No linting tools are configured - use `python -m py_compile` for basic syntax checking

## Common Tasks

The following are outputs from frequently run commands. Reference them instead of viewing, searching, or running bash commands to save time.

### Repository root
```
ls -la
.git/
.github/
.gitignore
.venv/                  # Created by setup.sh
fetch_transcript.py     # Main script for fetching YouTube transcripts
requirements.txt        # Python dependencies
setup.sh               # Environment setup script
test_imports.py         # Validation script for dependencies
transcript_qSGkJ_vsuUg.txt  # Example transcript file
youtube_summary.py      # Main script for generating summaries
```

### Python dependencies (requirements.txt)
```
youtube-transcript-api  # Primary transcript fetching
pafy                   # Fallback transcript fetching + metadata
youtube_dl             # Backend for pafy
pytube                 # Secondary fallback for transcript fetching
openai>=0.27.0         # AI summarization
yt-dlp                 # Additional YouTube downloading capability
```

### Script arguments
```
fetch_transcript.py:
  --video_id (required): YouTube video ID (e.g., qSGkJ_vsuUg)
  --output (required): Path to output transcript file

youtube_summary.py:
  --input (required): Path to transcript file
  --output (required): Path to output markdown file
  --video_id (required): YouTube video ID for summary title
```

### Common error patterns
- `OpenAIError: The api_key client option must be set` -- Missing OPENAI_API_KEY environment variable
- `No address associated with hostname` -- Network connectivity issues or sandbox limitations
- `No transcript found` -- Video has no available transcripts or is private/deleted
- `TRANSCRIPT_NOT_FOUND` written to file -- All transcript fetching methods failed
- `ModuleNotFoundError` during import -- Dependencies not installed, setup.sh may have failed
- `ReadTimeoutError` during pip install -- Network timeout, increase timeout or retry
- Network limitations in sandboxed environments prevent YouTube access and pip installations

### Troubleshooting scenarios
- **Network-limited environment**: Use existing `transcript_qSGkJ_vsuUg.txt` for testing summary generation
- **Missing dependencies**: Use `python -m py_compile` for syntax validation, focus on code structure
- **API key testing**: Set `export OPENAI_API_KEY=test_key` to test argument parsing (will fail at API call)
- **File processing**: Test with sample data using file I/O operations and encoding handling
- **Command line testing**: Use `python script.py --help` to validate argument parsing (requires dependencies)

### File structure expectations
- Input: YouTube video ID (11-character string)
- Transcript output: Plain text file with metadata header + transcript content
- Summary output: Markdown file with emoji-enhanced summary and video ID in title
- All files use UTF-8 encoding with error handling for non-standard characters

## Working with the Code

### fetch_transcript.py structure
- Uses argparse for command-line arguments
- Attempts metadata fetching via pafy (may fail in restricted environments)
- Primary transcript fetching via youtube_transcript_api with translation fallback
- Secondary fallback via pytube with SRT caption parsing
- Writes metadata + transcript content to output file, or "TRANSCRIPT_NOT_FOUND" on failure

### youtube_summary.py structure
- Reads transcript from input file with UTF-8 encoding and error replacement
- Creates OpenAI client with environment variable API key
- Uses gpt-4.1-mini model with custom instructions for emoji-rich markdown summaries
- Writes summary directly to output file

### Key dependencies behavior
- youtube_transcript_api: Primary method, supports auto-translation
- pytube: Fallback method, extracts SRT captions and filters timing info
- pafy: Metadata extraction (may fail in sandboxed environments)
- openai: Requires valid API key, fails immediately if not set

### Modification guidelines
- Always preserve the fallback chain in fetch_transcript.py
- Always handle UTF-8 encoding properly for international video content
- Always validate that error cases write appropriate content to output files
- Test with both working and non-working video IDs to verify error handling
- Consider network limitations when testing in sandboxed environments

### Environment limitations and workarounds
- **Sandboxed environments**: May lack internet access for YouTube or PyPI
- **Network timeouts**: pip install may fail - document as known limitation
- **Testing without dependencies**: Focus on syntax, structure, and logic validation
- **API testing**: Use mock data or existing sample files for development
- **Validation strategy**: Prioritize code compilation and file I/O testing over full workflow execution