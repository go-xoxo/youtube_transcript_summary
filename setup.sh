#!/usr/bin/env bash
set -euo pipefail

echo "Setting up YouTube Transcript Summary environment..."

# Check if requirements.txt exists
if [ ! -f requirements.txt ]; then
    echo "ERROR: requirements.txt not found. Cannot install Python dependencies."
    echo "Please ensure you are running this script from the project root directory."
    exit 1
fi

# Create and activate a Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# If there's a package.json, install JS dependencies
if [ -f package.json ]; then
    echo "Installing JavaScript dependencies..."
    if ! npm install; then
        echo "WARNING: npm install failed. JavaScript dependencies may not be available."
        echo "This may not affect core functionality if you only need Python features."
        echo "Check if Node.js and npm are properly installed."
    fi
fi

# If there's an auxiliary setup script, run it
if [ -x run/setup.sh ]; then
    echo "Running auxiliary setup script..."
    bash run/setup.sh
fi

echo ""
echo "Setup complete!"
echo ""
echo "To start using the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To deactivate the virtual environment when done:"
echo "  deactivate"
echo ""
echo "Don't forget to set your OpenAI API key:" 
echo "  export OPENAI_API_KEY=<your_key>"
echo ""
echo "Example usage:"
echo "  python fetch_transcript.py --video_id dQw4w9WgXcQ --output transcript.txt"
echo "  python youtube_summary.py --input transcript.txt --output summary.md --video_id dQw4w9WgXcQ"