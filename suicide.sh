#!/bin/bash

# This script removes all traces of the specified directory and its contents,
# and removes any references to it from logs.

# Define the directory to be removed
TARGET_DIR="."
LOG_FILES=("/var/log/syslog" "/var/log/auth.log")  # Add more log files if needed

# Check if the directory exists
if [ -d "$TARGET_DIR" ]; then
    # Remove the directory and its contents
    rm -rf "$TARGET_DIR"
    echo "Directory $TARGET_DIR and its contents have been removed."
else
    echo "Directory $TARGET_DIR does not exist."
fi

# Remove references to the directory from log files
for LOG_FILE in "${LOG_FILES[@]}"; then
    if [ -f "$LOG_FILE" ]; then
        sed -i "/$TARGET_DIR/d" "$LOG_FILE"
        echo "References to $TARGET_DIR have been removed from $LOG_FILE."
    else
        echo "Log file $LOG_FILE does not exist."
    fi
done