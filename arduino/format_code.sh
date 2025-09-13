#!/bin/bash
# Format all Arduino C++ files using clang-format
# Usage: ./format_code.sh [--check]

set -e

ARDUINO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLANG_FORMAT_CONFIG="$ARDUINO_DIR/.clang-format"

# Check if clang-format is installed
if ! command -v clang-format &> /dev/null; then
    echo "Error: clang-format is not installed"
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt install clang-format"
    echo "  macOS: brew install clang-format"
    echo "  Fedora: sudo dnf install clang-tools-extra"
    exit 1
fi

# Check if .clang-format exists
if [[ ! -f "$CLANG_FORMAT_CONFIG" ]]; then
    echo "Error: .clang-format not found at $CLANG_FORMAT_CONFIG"
    exit 1
fi

echo "Arduino Code Formatter"
echo "======================"
echo "Using config: $CLANG_FORMAT_CONFIG"
echo "Working directory: $ARDUINO_DIR"
echo

# Find all Arduino source files
SOURCE_FILES=($(find "$ARDUINO_DIR" -name "*.ino" -o -name "*.cpp" -o -name "*.h" -o -name "*.hpp" | grep -v ".git"))

if [[ ${#SOURCE_FILES[@]} -eq 0 ]]; then
    echo "No Arduino source files found"
    exit 0
fi

echo "Found ${#SOURCE_FILES[@]} source files:"
for file in "${SOURCE_FILES[@]}"; do
    echo "  $(basename "$file")"
done
echo

# Check mode (dry run)
if [[ "$1" == "--check" ]]; then
    echo "Running format check (no files will be modified)..."
    EXIT_CODE=0
    
    for file in "${SOURCE_FILES[@]}"; do
        if ! clang-format --dry-run --Werror --style=file:"$CLANG_FORMAT_CONFIG" "$file" 2>/dev/null; then
            echo "❌ $(basename "$file") - needs formatting"
            EXIT_CODE=1
        else
            echo "✅ $(basename "$file") - properly formatted"
        fi
    done
    
    if [[ $EXIT_CODE -eq 0 ]]; then
        echo
        echo "✅ All files are properly formatted!"
    else
        echo
        echo "❌ Some files need formatting. Run './format_code.sh' to fix."
    fi
    
    exit $EXIT_CODE
fi

# Format mode
echo "Formatting files..."
FORMATTED_COUNT=0

for file in "${SOURCE_FILES[@]}"; do
    # Create backup
    cp "$file" "$file.bak"
    
    # Format the file
    if clang-format --style=file:"$CLANG_FORMAT_CONFIG" -i "$file"; then
        # Check if file was actually changed
        if ! cmp -s "$file" "$file.bak"; then
            echo "✅ Formatted: $(basename "$file")"
            ((FORMATTED_COUNT++))
        else
            echo "   No change: $(basename "$file")"
        fi
    else
        echo "❌ Error formatting: $(basename "$file")"
        # Restore backup on error
        mv "$file.bak" "$file"
        continue
    fi
    
    # Remove backup if successful
    rm "$file.bak"
done

echo
echo "Formatting complete!"
echo "Files formatted: $FORMATTED_COUNT/${#SOURCE_FILES[@]}"

if [[ $FORMATTED_COUNT -gt 0 ]]; then
    echo
    echo "Tip: Review the changes with 'git diff' before committing"
fi