#!/bin/bash
# run_ar_workspace.sh

# 1. Define Project Directory
PROJECT_DIR="/Users/olegfylypczuk/.gemini/antigravity/scratch/holographic_ar_workspace"
cd "$PROJECT_DIR" || exit

# 2. Check if .venv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# 3. Activate venv
source .venv/bin/activate

# 4. Install Dependencies (Quietly)
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet opencv-python mediapipe numpy

# 5. Run the Application
echo "Starting Holographic AR Workspace..."
python3 ar_workspace.py


