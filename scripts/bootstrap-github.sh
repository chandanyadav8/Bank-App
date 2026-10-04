#!/usr/bin/env bash
# Creates GitHub repo and pushes (run on your Mac or any machine with gh auth login)
set -euo pipefail

REPO_NAME="voice-mock-test-assistant"
OWNER="${GITHUB_OWNER:-chandanyadav8}"

cd "$(dirname "$0")/.."

if gh repo view "$OWNER/$REPO_NAME" &>/dev/null; then
  echo "Repo $OWNER/$REPO_NAME already exists."
else
  echo "Creating $OWNER/$REPO_NAME..."
  gh repo create "$OWNER/$REPO_NAME" \
    --public \
    --description "Voice mock test assistant for Java interviews - web + iOS" \
    --source=. \
    --remote=origin
fi

git push -u origin main
echo "Done! https://github.com/$OWNER/$REPO_NAME"
