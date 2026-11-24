#!/usr/bin/env bash
set -u

# Use the available CPU count on Linux, with a macOS fallback.
if ! num_copies=$(nproc 2>/dev/null); then
    num_copies=$(sysctl -n hw.logicalcpu) || exit 1
fi
[[ $num_copies =~ ^[1-9][0-9]*$ ]] || exit 1

pids=()

for ((i = 1; i <= num_copies; i++)); do
    label="xxx-$i"
    WORKER_LABEL="$label" nohup python3 runner.py \
        </dev/null >>"log-$label.log" 2>&1 &
    pids[i]=$!
    printf 'Started %s (PID %s)\n' "$label" "${pids[i]}"
done

status=0
for ((i = 1; i <= num_copies; i++)); do
    if wait "${pids[i]}"; then
        printf 'xxx-%d (PID %s) finished\n' "$i" "${pids[i]}"
    else
        rc=$?
        printf 'xxx-%d (PID %s) exited with status %d\n' \
            "$i" "${pids[i]}" "$rc" >&2
        status=1
    fi
done
exit "$status"
