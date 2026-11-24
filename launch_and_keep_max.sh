#!/usr/bin/env bash
set -eu

cd -- "$(dirname -- "$0")"

MIN_TARGET=70
MAX_CAP=90
COOLDOWN_SEC=5
RESTART_BACKOFF_SEC=3

num_cpus=$(nproc)
[[ $num_cpus =~ ^[1-9][0-9]*$ ]] || { echo "Invalid CPU count: $num_cpus" >&2; exit 1; }
MIN_WORKERS="$num_cpus"
MAX_WORKERS=$((num_cpus * 4))

declare -a pids=()
declare -a labels=()
declare -A pid_to_label=()
next_idx=1
last_scale_ts=0
last_exit_ts=0

start_one_worker() {
    local label="${1:-}"
    if [[ -z "$label" ]]; then
        label="xxx-${next_idx}"
        next_idx=$((next_idx + 1))
    fi
    local log_file="log-${label}.log"

    WORKER_LABEL="$label" \
    WORKER_CPU_MIN="$MIN_TARGET" \
    WORKER_CPU_MAX="$MAX_CAP" \
    nohup python3 runner.py \
        </dev/null >>"$log_file" 2>&1 &
    local pid=$!

    if [[ -n "$pid" ]]; then
        pids+=("$pid")
        labels+=("$label")
        pid_to_label["$pid"]="$label"
        printf '[start] Started %s (PID %s), logging to %s\n' "$label" "$pid" "$log_file"
    fi
}

stop_one_worker() {
    local count=${#pids[@]}
    (( count > 1 )) || return 1

    local last_i=$((count - 1))
    local pid="${pids[$last_i]:-}"
    local label="${labels[$last_i]:-worker}"

    unset 'pids[last_i]' 'labels[last_i]'
    if (( ${#pids[@]} > 0 )); then
        pids=("${pids[@]}")
        labels=("${labels[@]}")
    else
        pids=()
        labels=()
    fi

    if [[ -n "$pid" ]]; then
        unset "pid_to_label[$pid]" || true
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
        fi
        printf '[scale-down] Stopped %s (PID %s)\n' "$label" "$pid"
        return 0
    fi
    return 1
}

reap_and_restart_workers() {
    local new_pids=()
    local new_labels=()
    local exited_labels=()
    local i pid label rc now

    for i in "${!pids[@]}"; do
        pid="${pids[$i]:-}"
        label="${labels[$i]:-worker}"
        [[ -n "$pid" ]] || continue

        if kill -0 "$pid" 2>/dev/null; then
            new_pids+=("$pid")
            new_labels+=("$label")
        else
            if wait "$pid" 2>/dev/null; then
                printf '%s (PID %s) exited cleanly\n' "$label" "$pid"
            else
                rc=$?
                printf '%s (PID %s) exited with status %d\n' "$label" "$pid" "$rc" >&2
            fi
            unset "pid_to_label[$pid]" || true
            exited_labels+=("$label")
        fi
    done

    if (( ${#new_pids[@]} > 0 )); then
        pids=("${new_pids[@]}")
        labels=("${new_labels[@]}")
    else
        pids=()
        labels=()
    fi

    if (( ${#exited_labels[@]} > 0 )); then
        last_exit_ts=$(date +%s)
        for label in "${exited_labels[@]}"; do
            printf '[restart-queued] Will restart %s after %ss backoff\n' "$label" "$RESTART_BACKOFF_SEC"
        done
    fi

    now=$(date +%s)
    if (( ${#pids[@]} < MIN_WORKERS )) && (( now - last_exit_ts >= RESTART_BACKOFF_SEC )); then
        local needed=$((MIN_WORKERS - ${#pids[@]}))
        local k
        for ((k = 0; k < needed; k++)); do
            start_one_worker
        done
        last_exit_ts=$now
    fi
}

cleanup_all() {
    local pid label
    for pid in "${pids[@]:-}"; do
        [[ -n "$pid" ]] || continue
        label="${pid_to_label[$pid]:-worker}"
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
            printf 'Stopped %s (PID %s)\n' "$label" "$pid"
        fi
    done
}
trap cleanup_all EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

read_cpu() {
    local cpu user nice system idle iowait irq softirq steal rest
    read -r cpu user nice system idle iowait irq softirq steal rest < /proc/stat
    total=$((user + nice + system + idle + iowait + irq + softirq + steal))
    idle_total=$((idle + iowait))
}

for ((i = 1; i <= num_cpus; i++)); do
    start_one_worker
done

read_cpu
while true; do
    sleep 1
    reap_and_restart_workers

    prev_total=$total
    prev_idle=$idle_total
    read_cpu

    elapsed=$((total - prev_total))
    (( elapsed > 0 )) || continue
    busy=$((elapsed - (idle_total - prev_idle)))
    host_pct=$((100 * busy / elapsed))
    now=$(date +%s)

    if (( host_pct < MIN_TARGET )); then
        if (( now - last_scale_ts >= COOLDOWN_SEC )) && (( ${#pids[@]} < MAX_WORKERS )); then
            start_one_worker
            last_scale_ts=$now
        fi
        printf 'Host CPU: %d%% [BELOW %d%%, active workers: %d]\n' "$host_pct" "$MIN_TARGET" "${#pids[@]}"
    elif (( host_pct > MAX_CAP )); then
        if (( now - last_scale_ts >= COOLDOWN_SEC )); then
            if stop_one_worker; then
                last_scale_ts=$now
            fi
        fi
        printf 'Host CPU: %d%% [ABOVE %d%%, active workers: %d]\n' "$host_pct" "$MAX_CAP" "${#pids[@]}"
    else
        printf 'Host CPU: %d%% [IN %d-%d%%, active workers: %d]\n' "$host_pct" "$MIN_TARGET" "$MAX_CAP" "${#pids[@]}"
    fi
done
