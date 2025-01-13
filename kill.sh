#!/usr/bin/env bash
#
# Kills all processes started by start.sh and launch_and_keep_max.sh forcefully.
#
# Returns
# -------
# None
#
# Raises
# ------
# No exceptions are raised
#

pkill -9 -f "bash ./launch_and_keep_max.sh"
pkill -9 -f "python3 runner.py"
pkill -9 -f "bash ./start.sh"
pkill -9 -f "python3 runner.py"