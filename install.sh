#!/bin/bash
set -e

echo ""
echo "=================================================="
echo "  Compound Brain — One-Line Install"
echo "=================================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Install Python 3.9+ first."
    exit 1
fi

# Clone if not already in the repo
if [ ! -f "main.py" ]; then
    git clone https://github.com/challengekim/compound-brain.git
    cd compound-brain
fi

# Create virtual environment and install
python3 -m venv .venv 2>/dev/null && source .venv/bin/activate 2>/dev/null
pip install -r requirements.txt

# Run setup wizard
python3 setup_wizard.py

echo ""
echo "Done! Run: python3 main.py"
