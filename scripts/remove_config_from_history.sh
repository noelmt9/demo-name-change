#!/bin/bash
# Script to remove config.py from git history
# WARNING: This rewrites git history. Use with caution.

echo "⚠️  WARNING: This will rewrite your git history!"
echo "This script will remove config.py from all git commits."
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo "Removing config.py from git history..."

# Remove config.py from git history using filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch config.py" \
  --prune-empty --tag-name-filter cat -- --all

echo ""
echo "✅ Done! config.py has been removed from git history."
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "1. Force push to update remote: git push --force --all"
echo "2. Force push tags: git push --force --tags"
echo "3. ROTATE YOUR API KEYS immediately - they were exposed in git history!"
echo "   - VAPI: Generate new API key in VAPI dashboard"
echo "   - OpenAI: Revoke old key and create new one in OpenAI platform"
echo ""
echo "⚠️  If others have cloned this repo, they need to:"
echo "   git fetch origin"
echo "   git reset --hard origin/main"

