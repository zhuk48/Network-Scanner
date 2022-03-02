## RUN PROGRAM: python3 scan.py [input_file.txt] [output_file.json]

import json
import string
import time
import json
import sys

webpages = {} # dictionary that holds webpages and the corresponding dictionary for that site

# reads input file
def fill_to_scan(user_in):
    with open(user_in) as fp:
        while True:
            line = fp.readline()
            line = line.strip()
            if not line:
                break
            else:
                webpages[line] = {}

# writes output file
def fill_json_out(file_name):
    #json_obj = json.dumps(webpages)
    with open(file_name, "w") as f:
        json.dump(webpages, f, sort_keys=True, indent=4)

def scan_sites():
    for page in webpages:
        curr_time = get_time()
        webpages[page]["scan_time"] = curr_time

## functions to fill respective information
def get_time():
    return time.time()

user_in = sys.argv[1]
user_out = sys.argv[2]
fill_to_scan(user_in)
scan_sites()
fill_json_out(user_out)
