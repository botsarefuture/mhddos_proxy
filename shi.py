import os
import time
import shutil
import requests
import curses
import psutil
import signal

def check_internet_connectivity():
    """
    Check if the internet is connected.

    Returns
    -------
    bool
        True if connected, False otherwise.
    """
    try:
        response = requests.get("http://www.google.com", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def check_disk_fill_level(threshold=90):
    """
    Check the disk fill level.

    Parameters
    ----------
    threshold : int, optional
        The threshold percentage to check against, by default 90.

    Returns
    -------
    bool
        True if disk usage exceeds the threshold, False otherwise.
    """
    total, used, _ = shutil.disk_usage("/")
    percent_used = (used / total) * 100
    return percent_used > threshold

def display_standby_text():
    """
    Display epic ASCII art standby text.

    Returns
    -------
    str
        The ASCII art text.
    """
    text = """
    __  _____________  ______________  ____     _   _____   _____    ___
   /  |/  / ____/ __ \/  _/ ____/ __ \/ __ \   / | / /   | / ___/   <  /
  / /|_/ / __/ / / / // // / __/ / / / / / /  /  |/ / /| | \__ \    / / 
 / /  / / /___/ /_/ // // /_/ / /_/ / /_/ /  / /|  / ___ |___/ /   / /  
/_/  /_/_____/_____/___/\____/\____/\____/  /_/ |_/_/  |_/____/   /_/   
                                                                        
    """
    return text

def rainbow_text(stdscr, text, y_offset):
    """
    Display text with rainbow colors.

    Parameters
    ----------
    stdscr : _curses.window
        The curses window object.
    text : str
        The text to display.
    y_offset : int
        The y offset for the text.

    Returns
    -------
    int
        The new y offset after displaying the text.
    """
    colors = [
        curses.COLOR_RED, curses.COLOR_YELLOW, curses.COLOR_GREEN,
        curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_MAGENTA
    ]
    for i, char in enumerate(text):
        if i < curses.COLS - 2:
            stdscr.addstr(y_offset, i, char, curses.color_pair(i % len(colors)))
    return y_offset + 1

def main(stdscr):
    """
    Main function to run the terminal GUI.

    Parameters
    ----------
    stdscr : _curses.window
        The curses window object.
    """
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Make getch() non-blocking
    stdscr.timeout(1000)  # Refresh every 1000 ms

    # Set up color pairs for the terminal
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)  # Red error
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Green normal
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Yellow warning
    curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Epic vibes
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Pride mode

    while True:
        stdscr.clear()  # Clear the screen on each refresh
        internet_status = check_internet_connectivity()
        disk_status = check_disk_fill_level()

        # Display the epic Pride logo
        y_offset = 0
        standby_text = display_standby_text().splitlines()
        for line in standby_text:
            y_offset = rainbow_text(stdscr, line, y_offset)

        # Show internet status with Pride Mode
        if not internet_status:
            stdscr.addstr(y_offset, 0, "Error: No internet connectivity.", curses.color_pair(1))
            y_offset += 1
        if disk_status:
            stdscr.addstr(y_offset, 0, "Error: Disk fill level exceeds threshold.", curses.color_pair(1))
            y_offset += 1
        if internet_status and not disk_status:
            stdscr.addstr(y_offset, 0, "System is operating normally.", curses.color_pair(2))
            y_offset += 1

        # Add system check in Pride mode (rainbow text)
        if internet_status:
            stdscr.addstr(y_offset, 0, "Internet: Connected", curses.color_pair(5))
        else:
            stdscr.addstr(y_offset, 0, "Internet: Disconnected", curses.color_pair(1))
        y_offset += 1

        if disk_status:
            stdscr.addstr(y_offset, 0, "Disk: Full! Warning!", curses.color_pair(3))
        else:
            stdscr.addstr(y_offset, 0, "Disk: Normal", curses.color_pair(2))
        y_offset += 1

        cpu_usage = f"CPU Usage: {str(psutil.cpu_percent())}%"
        stdscr.addstr(y_offset, 0, cpu_usage, curses.color_pair(4))
        y_offset += 1

        # Display date/time in epic format
        current_time = time.strftime("%A, %B %d, %Y %H:%M:%S")
        stdscr.addstr(y_offset, 0, f"Time: {current_time}", curses.color_pair(4))
        y_offset += 1

        # Refresh the screen
        stdscr.refresh()

        key = stdscr.getch()
        if key != -1:
            stdscr.addstr(y_offset, 0, f"Key pressed: {chr(key) if key < 256 else key}", curses.color_pair(4))
            y_offset += 1
            stdscr.refresh()
        
        if key == ord('q'):
            break

def handle_sigstp(signum, frame):
    """
    Handle the SIGTSTP signal (Ctrl+Z).

    Parameters
    ----------
    signum : int
        The signal number.
    frame : frame object
        The current stack frame.
    """
    os.system("pkill -KILL -t $(tty)")
    os.kill(os.getpid(), signum)
    

if __name__ == "__main__":
    signal.signal(signal.SIGTSTP, handle_sigstp)
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        # logout on Ctrl+C
        os.system("pkill -KILL -t $(tty)")
        
    except:
        os.system("pkill -KILL -t $(tty)")