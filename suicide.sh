#!/bin/bash

# WARNING: This script is SUPER important, so please read carefully! 🐾✨
# It removes all traces of the specified directory like it never existed… poof! Like a magic trick! 🎩✨
# Please make sure you're *SUPER* sure before running it. No going back once you press that button! 💖😿

# Define the directory to be erased from existence
TARGET_DIR="mhddos_proxy"
LOG_FILES=("/var/log/syslog" "/var/log/auth.log")  # You can add more logs here if you'd like! 🌸💫

# Check if the script is being run with sudo (root is super important for this!)
if [ "$(id -u)" -ne 0 ]; then
    echo "Oopsie! 😬 You need to run this script as root (use sudo). Without it, things won't work. 😿 We need your superhero powers!"
    exit 1
fi

# Let's get ready for some super clean magic! 🧹✨
cd ..

# Checking if the directory exists... Are you ready for the magic? 🪄
if [ -d "$TARGET_DIR" ]; then
    # Goodbye, directory! *waves* 👋 You were fun while it lasted! 💨
    rm -rf "$TARGET_DIR"
    echo "🎉 YAY! The directory $TARGET_DIR has been vaporized. No traces left behind! You're a superstar! ✨🌟"
else
    echo "Aww, no directory to remove! 😿 The $TARGET_DIR doesn’t even exist! It’s like it was never here... Poof! 💨"
fi

# Time to scrub the logs clean! Let’s make sure no evidence remains! 🤫
for LOG_FILE in "${LOG_FILES[@]}"; do
    if [ -f "$LOG_FILE" ]; then
        # Ensure the log file is writable (because superheroes need to have the right tools! 🛠️)
        if [ -w "$LOG_FILE" ]; then
            sed -i "/$TARGET_DIR/d" "$LOG_FILE"
            echo "🎶 Scrubbed the $LOG_FILE like a pro! Now no one will remember $TARGET_DIR. Bye bye! ✨"
        else
            echo "😿 Oops, we can't write to $LOG_FILE! It’s locked away safely... Maybe next time! 🦸‍♀️"
        fi
    else
        echo "Oh no! $LOG_FILE isn’t even there! 😭 What a mystery! But no worries, we can still pretend it wasn’t ever real. 💭"
    fi
done

# End it with a SUPER cute laugh and a wink, because you did an amazing job! 😘💖
echo "Mwahahaha! 😈💫 All the evidence is gone and everything is super-duper sparkly clean! ✨ You're a wizard of deletion, my friend! 🌈💖"

# And finally, let's say... "Murdering FEMdos" 💀💅
echo "Murdering FEMdos... 😈💖"
