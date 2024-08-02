#!/bin/bash

# Navigate to the project directory
cd /home/ubuntu/FirmwareExtractor

# Set remote URL to use SSH
echo "Updating remote URL to use SSH..."
git remote set-url origin git@github.com:Qiiks/FirmwareExtractor.git


# Find and kill the running process of your script
echo "Killing old process..."
pkill -f "main.py" || echo "No process found to kill."

# Wait a few seconds to ensure the process has terminated
sleep 3

# Fetch the latest changes from the remote repository
echo "Fetching latest changes..."
git fetch origin

# Check out only the updated file from the remote branch
echo "Updating NextBot V2.py..."
git checkout origin/main -- "main.py"

# Run the updated script in the background
echo "Starting updated script..."
nohup python3 "main.py" > /dev/null 2>&1 &

# Add and commit the JSON files if there are changes
echo "Committing JSON files..."
git add data.json
if git diff-index --quiet HEAD --; then
  echo "No JSON files to commit."
else
  git commit -m "Update JSON files [skip ci]"  # Prevent workflow triggers
  git push origin main
fi

echo "Deployment complete and script started"