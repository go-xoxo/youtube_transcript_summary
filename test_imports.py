#!/usr/bin/env python3
"""Simple test to verify imports work correctly"""

def test_imports():
    try:
        # Test fetch_transcript imports
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
        from xml.etree.ElementTree import ParseError
        import pafy
        from pytube import YouTube
        print("✓ fetch_transcript.py dependencies imported successfully")
        
        # Test youtube_summary imports
        import os
        import argparse
        from openai import OpenAI
        print("✓ youtube_summary.py dependencies imported successfully")
        
        # Test file reading
        transcript_path = '/home/runner/work/youtube_transcript_summary/youtube_transcript_summary/transcript_qSGkJ_vsuUg.txt'
        with open(transcript_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            print(f"✓ Successfully read transcript file ({len(content)} characters)")
        
        print("✓ All basic functionality tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)