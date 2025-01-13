#!/bin/bash

# WARNING: This script does what it says, so if you're not sure, stop now. Seriously, stop.
# It removes all traces of the specified directory like it never existed... kinda like your last Tinder date.

# Define the directory to be erased from existence
TARGET_DIR="mhddos_proxy"
LOG_FILES=("/var/log/syslog" "/var/log/auth.log")  # Also, if you want to go all out, add more logs. Go wild.

# Prepare to erase all evidence like a true spy movie villain
cd ..

# Check if the directory exists (spoiler: it better not by the end of this)
if [ -d "$TARGET_DIR" ]; then
    # Goodbye directory, you were never meant to be. *sniff*
    rm -rf "$TARGET_DIR"
    echo "BOOM! The directory $TARGET_DIR and everything inside it are now vaporized. No one will ever know."
else
    echo "Oopsie daisy! The directory $TARGET_DIR doesn’t even exist. It's like it was never here... well, technically it wasn’t."
fi

# Now we’re going to scrub the logs like your last embarrassing moment. Bye-bye evidence!
for LOG_FILE in "${LOG_FILES[@]}"; do
    if [ -f "$LOG_FILE" ]; then
        sed -i "/$TARGET_DIR/d" "$LOG_FILE"
        echo "Done. We just erased $TARGET_DIR from $LOG_FILE like it was a bad ex. Poof!"
    else
        echo "Whoops, no log file found at $LOG_FILE. Is this real life? Guess we just pretend it didn’t exist."
    fi
done

# Bonus points if you laugh maniacally after running this. 😈
