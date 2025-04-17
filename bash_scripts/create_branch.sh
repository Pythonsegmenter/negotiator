#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Prompt for the feature name
read -p "Enter the feature name: " feature_name

# Replace spaces with hyphens in the feature name
feature_name="${feature_name// /-}"

# Check out the 'main' branch
echo "Checking out 'main' branch..."
git checkout main

# Pull the latest changes from remote 'main'
echo "Pulling latest changes from 'origin/main'..."
git pull origin main

# Create a new branch with the provided feature name
echo "Creating new branch '$feature_name'..."
git checkout -b "$feature_name"

# Make an initial empty commit to ensure the branch has changes to push
echo "Making an initial commit..."
git commit --allow-empty -m "Initial commit for $feature_name"

# Push the new branch to the remote repository
echo "Pushing new branch to remote repository..."
git push -u origin "$feature_name"

echo "Branch '$feature_name' has been created and pushed to the remote repository."

echo "Update virtual environment"
pipenv install --dev
