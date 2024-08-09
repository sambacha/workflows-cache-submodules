#!/usr/bin/env python3
import os
import subprocess
import threading
from queue import Queue
from collections import namedtuple

# Define constants
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)

# Get submodules
SUBMODULES = [
    line.split("=", 1)[1].strip()
    for line in subprocess.check_output(["git", "config", "--list", "--file", ".gitmodules"], text=True).splitlines()
    if ".path=" in line
]

SLOW_SUBMODULES = [
    "lib/ds-test",
# TODO Add More
]

# Define TaskResult namedtuple
TaskResult = namedtuple("TaskResult", ["submodule", "output", "status"])

def run_process(*args):
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output, _ = process.communicate()
    return output, process.returncode

def update_submodule(submodule):
    output, status = run_process("git", "submodule", "update", "--", submodule)
    return TaskResult(submodule, output, status)

def run_thread(submodules, results):
    while True:
        try:
            submodule = submodules.get_nowait()
        except Queue.Empty:
            break
        results.put(update_submodule(submodule))

def main():
    submodules = Queue()
    results = Queue()

    # Update the slow submodules first
    sorted_submodules = sorted(SUBMODULES, key=lambda x: x not in SLOW_SUBMODULES)
    for submodule in sorted_submodules:
        submodules.put(submodule)

    # Create and start threads
    num_threads = 8 if len(sys.argv) < 2 else int(sys.argv[1])
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=run_thread, args=(submodules, results))
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Process results
    success = True
    for _ in range(len(SUBMODULES)):
        result = results.get()
        if result.status != 0:
            success = False
            print(f"Error updating {result.submodule}")
        if result.output.strip():
            print(result.output)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    import sys
    main()
