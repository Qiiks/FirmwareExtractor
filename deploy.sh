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
echo "Fetching latest changes and updating..."
git pull origin main

echo "Starting updated script..."
nohup python3 "NextBot V2.py" > /dev/null 2>&1 &

echo "Deployment complete and script started"