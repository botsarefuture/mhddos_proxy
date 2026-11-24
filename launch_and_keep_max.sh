#!/usr/bin/env bash
set -eu

read_cpu() {
    local cpu user nice system idle iowait irq softirq steal rest
    read -r cpu user nice system idle iowait irq softirq steal rest < /proc/stat
    total=$((user + nice + system + idle + iowait + irq + softirq + steal))
    idle_total=$((idle + iowait))
}

read_cpu
while sleep 1; do
    prev_total=$total
    prev_idle=$idle_total
    read_cpu

    elapsed=$((total - prev_total))
    (( elapsed > 0 )) || continue
    busy=$((elapsed - (idle_total - prev_idle)))
    printf 'Host CPU usage: %d%%\n' "$((100 * busy / elapsed))"
done
