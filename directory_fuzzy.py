# Author: AuxGrep
# 2025

import argparse
import requests
import concurrent.futures
import logging
import platform
import sys
import os
from io import StringIO
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from colorama import Fore, Style

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

console = Console()

# check os
def computer_check(supported=None):
    if supported is None:
        supported = ['windows', 'linux', 'darwin']
    current_os = platform.system().lower()
    if current_os in supported:
        logging.info(f"Started on [{current_os.capitalize()}]")
    else:
        logging.error(f"Unsupported OS: [{current_os.capitalize()}]")
        sys.exit(1)

# check wordlist
def fetch_wordlist(wordlist):
    if wordlist.startswith("http://") or wordlist.startswith("https://"):
        try:
            console.print(f"[cyan]Processing wordlist from:[/] {wordlist}")
            response = requests.get(wordlist, timeout=10)
            response.raise_for_status()
            return response.text.splitlines()  
        except requests.RequestException as e:
            console.print(f"[red]Error processing wordlist:[/] {e}")
            sys.exit(1)
    elif os.path.exists(wordlist):
        with open(wordlist, "r") as file:
            return [line.strip() for line in file if line.strip()]
    else:
        console.print(f"[red]Wordlist file not found:[/] {wordlist}")
        sys.exit(1)

# Check if a URL exists and return its status.
def check_url(target, path, progress, task):
    full_url = f"{target}/{path.strip()}"
    try:
        resp = requests.get(full_url, timeout=5)
        status = f"{resp.status_code} {resp.reason}"

        # Show real-time checking logs
        console.print(f"[yellow]CHECKING:[/] {full_url} ({status})")

        if resp.status_code == 200:
            with open("found.txt", "a") as f:
                f.write(f"{full_url} ({status}) - Path: {path}\n") 
            return full_url, status, path
    except requests.RequestException:
        console.print(f"[red]ERROR:[/] {full_url} (Request Failed)")

    # Return None if not 200
    progress.update(task, advance=1)
    return None, None, None  

# Get wordlist from local or URL
def web_directory(target, wordlist):
    urls = fetch_wordlist(wordlist)  

    table = Table(title=f"Found Directories on {target}")
    table.add_column("URL", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Path Tested", style="yellow")

    found_urls = []

    # Clear previous found.txt file
    open("found.txt", "w").close()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Scanning URLs...", total=len(urls))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(lambda url: check_url(target, url, progress, task), urls)
            for result in results:
                if result[0]:  
                    table.add_row(result[0], result[1], result[2])
                    found_urls.append(result)

    # Show results
    if found_urls:
        console.print(table)
    else:
        console.print("[red]No valid directories found.[/]")

def main():
    parser = argparse.ArgumentParser(description="Directory Fuzzy v1.0 || Author: AuxGrep")
    parser.add_argument("-u", "--url", required=True, help="Target URL (e.g., https://example.com)")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to local file or URL (e.g., http://example.com/wordlist.txt)")
    args = parser.parse_args()

    computer_check()
    web_directory(args.url, args.wordlist)

if __name__ == "__main__":
    main()
