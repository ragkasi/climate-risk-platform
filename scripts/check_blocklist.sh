#!/bin/bash

# Blocklist check script
# This script checks for blocked characters (em dashes, en dashes, emojis)

set -e

echo "Checking for blocked characters..."

# Find all tracked text files
FILES=$(git ls-files | grep -E '\.(py|js|ts|tsx|md|txt|json|yaml|yml|toml|sh|sql)$' | grep -v node_modules | grep -v __pycache__ | grep -v .git)

VIOLATIONS=0

for file in $FILES; do
    if [ -f "$file" ]; then
        # Check for em dash (U+2014)
        if grep -q $'\xE2\x80\x94' "$file"; then
            echo "ERROR: Em dash found in $file"
            grep -n $'\xE2\x80\x94' "$file" | head -3
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
        
        # Check for en dash (U+2013)
        if grep -q $'\xE2\x80\x93' "$file"; then
            echo "ERROR: En dash found in $file"
            grep -n $'\xE2\x80\x93' "$file" | head -3
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
        
        # Check for emojis (conservative range)
        if grep -Pq '[\xF0\x9F\x80-\xF0\x9F\xBF\xF0\x9F\x8C-\xF0\x9F\xA6\xF0\x9F\xAA-\xF0\x9F\xBF]' "$file"; then
            echo "ERROR: Emojis found in $file"
            grep -Pn '[\xF0\x9F\x80-\xF0\x9F\xBF\xF0\x9F\x8C-\xF0\x9F\xA6\xF0\x9F\xAA-\xF0\x9F\xBF]' "$file" | head -3
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
        
        # Check for smart quotes
        if grep -q $'\xE2\x80\x9C\|xE2\x80\x9D\|xE2\x80\x98\|xE2\x80\x99' "$file"; then
            echo "ERROR: Smart quotes found in $file"
            grep -n $'\xE2\x80\x9C\|xE2\x80\x9D\|xE2\x80\x98\|xE2\x80\x99' "$file" | head -3
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    fi
done

if [ $VIOLATIONS -eq 0 ]; then
    echo "✓ No blocked characters found"
    exit 0
else
    echo "✗ Found $VIOLATIONS files with blocked characters"
    echo "Please replace em dashes with ' - ', en dashes with ' - ', and remove emojis"
    exit 1
fi
