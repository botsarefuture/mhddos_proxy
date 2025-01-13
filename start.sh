#!/usr/bin/env bash
#
# Runs launch_and_keep_max.sh in the background forever and restarts if needed.
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

while true; do
    if ! pgrep -f "bash $script_path" > /dev/null; then
        nohup bash "$script_path" > /dev/null 2>&1 &
    fi
    sleep 5
done