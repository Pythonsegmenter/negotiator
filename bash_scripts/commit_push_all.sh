#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Check if requirements.txt is up to date
pipfile_mtime=$(stat -c %Y Pipfile)
requirements_mtime=$(stat -c %Y requirements.txt)

if [ "$requirements_mtime" -lt "$pipfile_mtime" ]; then
    echo "Updating requirements.txt..."
    pipenv requirements > requirements.txt
    echo "requirements.txt has been updated."
fi

# Prompt the user for the commit message
read -p "Enter commit message: " commit_message

# Add all changes
echo "Adding all changes..."
git add .

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
    echo "No changes to commit."
else
    # Commit with the provided message
    echo "Committing changes..."
    if ! git commit -m "$commit_message"; then
        # Retry adding and committing in case of formatting changes by hooks
        git add .
        git commit -m "$commit_message"
    fi
fi

# Push changes to the repository
echo "Pushing to repository..."
git push

echo "All changes have been committed and pushed successfully."
