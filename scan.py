## RUN PROGRAM: python3 scan.py [input_file.txt] [output_file.json]

import json
import string
import time
import json
import sys
import subprocess

webpages = {} # dictionary that holds webpages and the corresponding dictionary for that site
dns_resolvers = ["208.67.222.222", "1.1.1.1", "8.8.8.8", 
"8.26.56.26", "9.9.9.9", "64.6.65.6", "91.239.100.100", "185.228.168.168", 
"77.88.8.7", "156.154.70.1", "198.101.242.72", "176.103.130.130"]
#dns_resolvers = ["8.8.8.8"]

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
        # scan time
        curr_time = get_time()
        webpages[page]["scan_time"] = curr_time

        #IP addresses
        ip4, ip6 = get_ip(page)
        if ip4 == None or ip6 == None:
            pass
        else:
            webpages[page]['ipv4_addresses'] = ip4
            webpages[page]['ipv6_addresses'] = ip6

def run_cmd(cmd):
    result = ""
    try:
        result = subprocess.check_output(cmd, timeout=2, stderr=subprocess.STDOUT).decode("utf-8")
    except subprocess.TimeoutExpired:
        error_msg = "Command " + cmd[0] + " timed out"
        print(error_msg, file=sys.stderr)
    except FileNotFoundError:
        error_msg = "Command " + cmd[0] + " not found"
        print(error_msg, file=sys.stderr)
        result = None
    except:
        error_msg = "Unexpected error when running command " + cmd[0]
        print(error_msg, file=sys.stderr)
        result = ""
    return result

## functions to fill respective information
def get_time():
    return time.time()

def get_ip(page):
    ip4 = []
    ip6 = []
    cmd = ["nslookup", "", ""]
    for dns in dns_resolvers:
        cmd[1] = page
        cmd[2] = dns
        print(cmd)
        res = run_cmd(cmd)
        if res == "": # dns timeout or other error, skip and go to next dns
            continue
        if res == None: # command doesn't exist
            return None, None
        else:
            print(res)
            addrs = res.split("\n")
            for lines in addrs:
                if "Address" in lines:
                    if "#" in lines:
                        continue
                    if "." in lines:
                        a = lines.split(' ')
                        ip4.append(a[1].strip())
                        continue
                    if ":" in lines:
                        a = lines.split(' ')
                        ip6.append(a[1].strip())
    # Dropping not unique values by converting to set
    ip4set = set(ip4)
    ip6set = set(ip6)
    return list(ip4set), list(ip6set)
    

user_in = sys.argv[1]
user_out = sys.argv[2]
fill_to_scan(user_in)
scan_sites()
fill_json_out(user_out)