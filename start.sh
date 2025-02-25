#!/usr/bin/env bash
#
# FEMdos - Keeps things running smoothly, like a true diva. 💅✨
# Runs launch_and_keep_max.sh in the background forever and restarts if needed. 🌸
#
# Returns
# -------
# None
#
# Raises
# ------
# No exceptions are raised
#

script_path="./launch_and_keep_max.sh"

{
    # FEMdos is always on top of things, darling. Always ready to keep things running smoothly! 👑
    while true; do
        # Check if the script is running, if not, it’s time for a fabulous restart. 💁‍♀️💖
        if ! pgrep -f "bash $script_path" > /dev/null; then
            echo "Oops, darling! 😘 It looks like the script isn’t running. Let’s start it again, just like that! 💅"
            nohup bash "$script_path" > /dev/null 2>&1 &
        else
            echo "Yasss, queen! 👑 The script is already running, and everything is fabulous! 💖✨"
        fi
        # Giving it a cute little break before we check again, because even FEMdos deserves a moment of calm. 😌💆‍♀️
        sleep 5
    done
} &

# A sweet little message to let you know everything’s under control. 💖🌸
echo "Good day, darling! FEMdos has everything running smoothly and effortlessly! 💖💫"
exit 0
