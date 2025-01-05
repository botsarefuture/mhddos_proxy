#!/bin/bash

# """
# Launch and monitor multiple instances of runner.py in tmux sessions.
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

launch_session() {
    local session_name=$1
    tmux new-session -d -s "$session_name" "python3 runner.py"
    echo "Launched $session_name"
}

monitor_sessions() {
    while true; do
        for ((i=1; i<=num_copies; i++)); do
            session="xxx-$i"
            if ! tmux has-session -t "$session" 2>/dev/null; then
                echo "Session $session not found. Restarting."
                launch_session "$session"
            fi
        done
        sleep 5
    done
}

for ((i=1; i<=num_copies; i++)); do
    launch_session "xxx-$i"
    sleep 1
done

echo "Launched $num_copies instances of runner.py"
echo "To kill all instances, run 'tmux kill-session -a -t xxx-*'"

monitor_sessions &
