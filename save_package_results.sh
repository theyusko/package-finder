#!/bin/bash

# Check if at least output file and a package-finder argument is given
if [ $# -lt 2 ]; then
    echo "Usage: $0 <output_file> <arg1> [arg2] [arg3] ..."
    echo "Example: $0 package-finder-results.txt sc3 sc2 sc1"
    exit 1
fi

OUTPUT_FILE="$1"

# Shift to remove the output filename from arguments
shift

echo "Running package-finder with first argument: $1"
package-finder $1 > "$OUTPUT_FILE"

shift

# Process remaining arguments
while [ $# -gt 0 ]; do
    echo "Running package-finder with argument: $1"
    package-finder $1 >> "$OUTPUT_FILE"
    shift
done

echo "All commands completed. Results saved to $OUTPUT_FILE"