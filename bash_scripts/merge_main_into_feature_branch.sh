#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Get the current branch name
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Error: Uncommitted changes found. Please commit or stash your changes."
    exit 1
fi

# Check if upstream is set for the current branch
if ! git rev-parse --abbrev-ref "${current_branch}@{upstream}" >/dev/null 2>&1; then
    echo "Error: No upstream branch set for the current branch '$current_branch'."
    exit 1
fi

# Fetch the latest remote refs
echo "Fetching latest changes from remote..."
git fetch

# Check if the local branch is ahead of the remote branch
if [ "$(git rev-list "${current_branch}@{upstream}"..HEAD --count)" -ne 0 ]; then
    echo "Error: Local branch is ahead of remote. Please push your commits."
    exit 1
fi

# Check if the local branch is behind the remote branch
if [ "$(git rev-list HEAD.."${current_branch}@{upstream}" --count)" -ne 0 ]; then
    echo "Error: Local branch is behind remote. Please pull the latest changes."
    exit 1
fi

# All checks passed, proceed to merge
echo "Checking out 'main' branch..."
git checkout main

echo "Pulling latest changes from 'origin/main'..."
git pull origin main

echo "Switching back to '$current_branch'..."
git checkout "$current_branch"

echo "Merging 'main' into '$current_branch'..."
git merge main

echo "Merge completed successfully."
