#!/usr/bin/env bash
#
# Launches tasks to match the number of CPU cores and keeps them at maximum load.
#
# Returns
# -------
# None
#
# Raises
# ------
# No exceptions are raised
#

num_cores=$(nproc)

while true; do
    current_processes=$(pgrep -cf "python3 runner.py")
    cpu_usage=$(grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}')
    
    if [ "$current_processes" -lt "$num_cores" ] && (( $(echo "$cpu_usage < 90" | bc -l) )); then
        python3 runner.py &
    fi
    sleep 1
done