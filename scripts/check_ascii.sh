#!/bin/bash

# ASCII compliance check script
# This script checks that all tracked text files contain only ASCII characters

set -e

echo "Checking ASCII compliance..."

# Find all tracked text files
FILES=$(git ls-files | grep -E '\.(py|js|ts|tsx|md|txt|json|yaml|yml|toml|sh|sql)$' | grep -v node_modules | grep -v __pycache__ | grep -v .git)

VIOLATIONS=0

for file in $FILES; do
    if [ -f "$file" ]; then
        # Check if file contains non-ASCII characters
        if LC_ALL=C grep -q '[^ -~]' "$file"; then
            echo "ERROR: Non-ASCII characters found in $file"
            echo "Offending lines:"
            LC_ALL=C grep -n '[^ -~]' "$file" | head -5
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    fi
done

if [ $VIOLATIONS -eq 0 ]; then
    echo "✓ All files are ASCII compliant"
    exit 0
else
    echo "✗ Found $VIOLATIONS files with non-ASCII characters"
    echo "Please fix these files to contain only ASCII characters"
    exit 1
fi
