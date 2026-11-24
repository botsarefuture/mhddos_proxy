#!/usr/bin/env bash
set -eu

cd -- "$(dirname -- "$0")"

num_cpus=$(nproc)
[[ $num_cpus =~ ^[1-9][0-9]*$ ]] || { echo "Invalid CPU count: $num_cpus" >&2; exit 1; }

run_workers() {
    declare -A pid_to_label=()
    pids=()

    stop_children() {
        local pid
        for pid in "${pids[@]:-}"; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
            fi
        done
    }
    trap stop_children INT TERM

    for ((i = 1; i <= num_cpus; i++)); do
        label="xxx-$i"
        log_file="log-$label.log"

        WORKER_LABEL="$label" nohup python3 runner.py \
            </dev/null >>"$log_file" 2>&1 &
        pid=$!

        pids+=("$pid")
        pid_to_label["$pid"]="$label"
        printf 'Started %s (PID %s), logging to %s\n' "$label" "$pid" "$log_file"
    done

    overall_status=0
    for pid in "${pids[@]}"; do
        label="${pid_to_label[$pid]}"
        if wait "$pid"; then
            printf '%s (PID %s) exited cleanly\n' "$label" "$pid"
        else
            rc=$?
            printf '%s (PID %s) exited with status %d\n' "$label" "$pid" "$rc" >&2
            overall_status=1
        fi
    done

    exit "$overall_status"
}

if [[ "${1:-}" == "--run-workers" ]]; then
    run_workers
fi

quota=$((70 * num_cpus))
unit="runner-workers.service"
script_path="$PWD/$(basename -- "$0")"

cleanup_unit() {
    systemctl --user stop "$unit" 2>/dev/null || true
}
trap cleanup_unit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Start the worker service non-blockingly under a 70% aggregate CPU quota.
systemd-run --user --no-block --collect \
    --unit="$unit" \
    --working-directory="$PWD" \
    --property="CPUQuota=${quota}%" \
    -- /bin/bash "$script_path" --run-workers

read_cpu() {
    local cpu user nice system idle iowait irq softirq steal rest
    read -r cpu user nice system idle iowait irq softirq steal rest < /proc/stat
    total=$((user + nice + system + idle + iowait + irq + softirq + steal))
    idle_total=$((idle + iowait))
}

read_cpu
while systemctl --user is-active --quiet "$unit"; do
    prev_total=$total
    prev_idle=$idle_total
    sleep 1
    read_cpu

    elapsed=$((total - prev_total))
    (( elapsed > 0 )) || continue
    busy=$((elapsed - (idle_total - prev_idle)))
    printf 'Host CPU usage: %d%%\n' "$((100 * busy / elapsed))"
done
