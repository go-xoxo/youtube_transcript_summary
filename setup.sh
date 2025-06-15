#!/usr/bin/env bash
set -euo pipefail

# Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# If there's a package.json, install JS dependencies
if [ -f package.json ]; then
  npm install
fi

# If there's an auxiliary setup script, run it
if [ -x run/setup.sh ]; then
  bash run/setup.sh
fi

echo "Setup complete!"
echo "To start using the environment:"
echo "  source .venv/bin/activate"
echo "Don't forget to set your OpenAI API key:" \
     "export OPENAI_API_KEY=<your_key>"