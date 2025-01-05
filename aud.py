import argparse
import requests
import time
import logging
import signal
import sys
import threading
import socket
from flask import Flask, jsonify, render_template


app = Flask(__name__)
monitoring_results = {}


def parse_arguments():
    """
    Parse command line arguments.

    Returns
    -------
    args : argparse.Namespace
        Parsed arguments containing interval, timeout, log_file, and hosts_file.
    """
    parser = argparse.ArgumentParser(description="Query multiple domains at regular intervals.")
    parser.add_argument('--hosts_file', type=str, required=True, help='Path to hosts file')
    parser.add_argument('--interval', type=int, default=5, help='Interval between queries in seconds')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout for the HTTP request in seconds')
    parser.add_argument('--log_file', type=str, default=None, help='Path to log file')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Flask server host')
    parser.add_argument('--port', type=int, default=5000, help='Flask server port')
    return parser.parse_args()


def setup_logging(log_file=None):
    """
    Set up logging configuration.

    Parameters
    ----------
    log_file : str, optional
        Path to log file. If None, logs are printed to stdout.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='a'
    )
    if not log_file:
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)


def read_hosts(hosts_file):
    """
    Read hosts from the specified file.

    Parameters
    ----------
    hosts_file : str
        Path to the hosts file.

    Returns
    -------
    hosts : list of str
        List of domain names.
    """
    with open(hosts_file, 'r') as file:
        hosts = [line.strip() for line in file if line.strip()]
    return hosts


import cloudscraper


def query_domain(domain, timeout):
    """
    Query the specified domain once and measure response time, with Cloudflare bypass.

    Parameters
    ----------
    domain : str
        The domain to query.
    timeout : int
        Timeout for the HTTP request in seconds.

    Returns
    -------
    success : bool
        True if the query was successful, False otherwise.
    response_time : float or None
        Time taken to receive the response in seconds. None if the request fails.
    status_code : int or None
        HTTP status code received. None if the request fails.
    ip_address : str or None
        IP address that sent the response. None if the request fails.
    is_cloudflare : bool
        True if the response is from Cloudflare, False otherwise.
    """
    scraper = cloudscraper.create_scraper()
    url = domain if domain.startswith(('http://', 'https://')) else f'http://{domain}'
    try:
        start_time = time.time()
        response = scraper.get(url, timeout=timeout)
        end_time = time.time()
        response_time = end_time - start_time
        if domain.startswith('http://'):
            domain_clean = domain[7:]
        elif domain.startswith('https://'):
            domain_clean = domain[8:]
        else:
            domain_clean = domain

        ip_address = socket.gethostbyname(domain_clean)
        server_header = response.headers.get('Server', '').lower()
        is_cloudflare = 'cloudflare' in server_header
        return response.status_code == 200, response_time, response.status_code, ip_address, is_cloudflare
    except (requests.RequestException, socket.error, cloudscraper.exceptions.CloudflareChallengeError) as e:
        logging.error(f"Request failed for {domain}: {e}")
        return False, None, None, None, False


def monitor_domain(domain, interval, timeout):
    """
    Monitor a single domain at specified intervals.

    Parameters
    ----------
    domain : str
        The domain to monitor.
    interval : int
        Interval between queries in seconds.
    timeout : int
        Timeout for the HTTP request in seconds.
    """
    logging.info(f"Starting to monitor {domain} every {interval} seconds.")
    while True:
        success, response_time, status_code, ip_address, is_cloudflare = query_domain(domain, timeout)
        status = 'reachable' if success else 'unreachable'
        cloudflare_status = 'Cloudflare detected' if is_cloudflare else 'Cloudflare not detected'
        if response_time is not None and ip_address is not None:
            logging.info(f"{domain} is {status} (Status code: {status_code}, Response time: {response_time:.2f}s, IP: {ip_address}, {cloudflare_status})")
            monitoring_results[domain] = {
                'status': status,
                'status_code': status_code,
                'response_time': response_time,
                'ip_address': ip_address,
                'cloudflare': is_cloudflare
            }
        else:
            logging.info(f"{domain} is {status} (Status code: N/A, Response time: N/A, IP: N/A, {cloudflare_status})")
            monitoring_results[domain] = {
                'status': status,
                'status_code': None,
                'response_time': None,
                'ip_address': None,
                'cloudflare': is_cloudflare
            }
        time.sleep(interval)


@app.route('/status', methods=['GET'])
def get_status():
    """
    Get the current monitoring status of all domains.

    Returns
    -------
    response : JSON
        JSON representation of monitoring results.
    """
    return jsonify(monitoring_results)

@app.route("/")
def hello():
    return render_template('index.html')

def run_flask(host, port):
    """
    Run the Flask server.

    Parameters
    ----------
    host : str
        Host address.
    port : int
        Port number.
    """
    app.run(host=host, port=port, threaded=True)


def main():
    args = parse_arguments()
    setup_logging(args.log_file)
    hosts = read_hosts(args.hosts_file)

    def handle_exit(signum, frame):
        logging.info("Shutting down gracefully.")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    threads = []
    for host in hosts:
        thread = threading.Thread(target=monitor_domain, args=(host, args.interval, args.timeout))
        thread.start()
        threads.append(thread)

    flask_thread = threading.Thread(target=run_flask, args=(args.host, args.port))
    flask_thread.start()
    threads.append(flask_thread)

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()
