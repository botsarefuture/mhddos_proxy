#!/bin/bash

# """
# Launch and monitor multiple instances of runner.py using nohup with file logging.
#
# Parameters
# ----------
# None
#
# Returns
# -------
# None
# """

num_copies=$(nproc)

launch_process() {
    local process_name=$1
    local log_file="log-${process_name}.log"
    if ! pgrep -f "python3 runner.py" | grep -q "$process_name"; then
        nohup python3 runner.py > "$log_file" 2>&1 &
        echo "Launched $process_name"
    fi
}

monitor_processes() {
    while true; do
        for ((i=1; i<=num_copies; i++)); do
            process_name="xxx-$i"
            if ! pgrep -f "$process_name" > /dev/null; then
                echo "Process $process_name not found. Restarting."
                launch_process "$process_name"
            fi
        done
        sleep 5
    done
}

for ((i=1; i<=num_copies; i++)); do
    launch_process "xxx-$i"
    sleep 1
done

echo "Launched $num_copies instances of runner.py"
echo "To kill all instances, run 'pkill -f runner.py'"

monitor_processes &
