#!/bin/bash

git config --global user.name "StevoKeano"
git config --global user.email "ppsel03@gmail.com"
git config --global --list

# Start the SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa  # Adjust if your key has a different name

# Change to the directory where the Git repository is located
cd /home/stevo/TC2-BBS-mesh/mestastic-utils || exit


# Start the SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa  # Adjust if your key has a different name


# Check if a commit message is provided
if [ -z "$1" ]; then
  echo "Usage: ./push_changes.sh 'Your commit message'"
  exit 1
fi

# Stage all changes
git add .

# Commit the changes with the provided message
git commit -m "$1"

# Pull the latest changes from the remote repository
# Replace 'main' with your branch name if necessary
git pull origin main --allow-unrelated-histories

# Check if the pull was successful before pushing
if [ $? -eq 0 ]; then
  # Push the changes to the remote repository
  git push origin main
  echo "Changes have been pushed successfully."
else
  echo "Failed to pull the latest changes. Please resolve any conflicts."
fi

