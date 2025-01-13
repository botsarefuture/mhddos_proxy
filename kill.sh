#!/usr/bin/env bash
#
# Kills all processes started by start.sh and launch_and_keep_max.sh.
#
# Returns
# -------
# None
#
# Raises
# ------
# No exceptions are raised
#

pkill -f "bash ./launch_and_keep_max.sh"
pkill -f "python3 runner.py"
pkill -f "bash ./start.sh"
pkill -f "python3 runner.py"