## RUN PROGRAM: python3 scan.py [input_file.txt] [output_file.json]
## pip installed packages:
## - requests (https://docs.python-requests.org/en/master/user/install/)
## - dnspython (https://dnspython.readthedocs.io/en/stable/)
## - maxminddb
## - geopy ()

# ask at OH:
# 1. bad website causes crash when running nslookup
# 2. how to check for SSL? openssl doesn't support anymore

import json
import string
import time
import json
import sys
import os
import signal
import socket
import subprocess
import requests
from dns import resolver, reversename
import maxminddb
from geopy.geocoders import Nominatim

webpages = {} # dictionary that holds webpages and the corresponding dictionary for that site
#dns_resolvers = ["208.67.222.222", "1.1.1.1", "8.8.8.8", 
#"8.26.56.26", "9.9.9.9", "64.6.65.6", "91.239.100.100", "185.228.168.168", 
#"77.88.8.7", "156.154.70.1", "198.101.242.72", "176.103.130.130"]
# TESTING PURPOSED ONLY:
dns_resolvers = ["8.8.8.8"]

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
            continue
        else:
            webpages[page]['ipv4_addresses'] = ip4
            webpages[page]['ipv6_addresses'] = ip6

        #HTTP server
        webpages[page]["http_server"] = get_httpserver(page)

        #Allows HTTP requests?
        webpages[page]["insecure_http"] = get_insecure_http(page)

        #Redirects  HTTP to HTTPS?
        webpages[page]["redirect_to_https"] = get_redirect_https(page)

        #HSTS
        webpages[page]["hsts"] = get_hsts(page)

        #TLS
        webpages[page]["tls_versions"] = get_tls(page)

        #Root CA
        webpages[page]["root_ca"] = get_root_ca(page)

        #RDNS
        webpages[page]["rdns_names"] = get_rdns(ip4)

        #RTT
        webpages[page]["rtt_range"] = get_rtt(ip4)

        #Geo locations
        webpages[page]["geo_locations"] = get_geo_loc(ip4)

def run_cmd(cmd):
    result = ""
    try:
        result = subprocess.check_output(cmd, timeout=2, stderr=subprocess.STDOUT, input=b'').decode("utf-8")
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

# This modified subprocess function is required because subprocess by default will not kill any children
# function called, even after the time out. The function to get RTT calls a child function and hangs if telnet hangs.
# Taken from https://alexandra-zaharia.github.io/posts/kill-subprocess-and-its-children-on-timeout-python/
def run_cmd1(cmd):
    try:
        p = subprocess.Popen(cmd, start_new_session=True, stdout=subprocess.PIPE)
        p.wait(timeout=2)
        out = p.communicate()
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        errormsg = "Command " + cmd[0] + " timed out!"
        print(errormsg, file=sys.stderr)
        return None
    else:
        return out

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

def get_httpserver(page):
    page_https = "https://" + page
    page_http = "http://" + page
    
    try:
        r = requests.get(page_http, timeout=2, allow_redirects=False)
    except:
        try:
            r1 = requests.get(page_https, timeout=2, allow_redirects=False)
        except:
            print("responses library could not reach webpage " + page, file=sys.stderr)
            return None
        else:
            if 'server' in r1.headers:
                return r1.headers['server']
            else:
                return None
    else:
        if 'server' in r.headers:
            return r.headers['server']
        else:
            return None

def get_insecure_http(page):
    page = "http://" + page
    try:
        r = requests.get(page, timeout=2, allow_redirects=False)
    except requests.exceptions.HTTPError:
        return False
    else:
        return True
        
def get_redirect_https(page):
    page = "http://" + page
    try:
        r = requests.get(page, timeout=2, allow_redirects=False)
    except:
        print("responses library could not reach webpage " + page, file=sys.stderr)
        return False
    else:
        if int(r.status_code >= 300):
            redirect_to = r.headers['location']
            if "https" in redirect_to:
                return True
        else:
            return False
    
def get_hsts(page):
    page = "https://" + page
    try:
        r = requests.get(page, timeout=2, allow_redirects=True)
    except requests.exceptions.Timeout:
        print(page + " timed out", file=sys.stderr)
        return False
    except:
        print("responses library could not reach webpage " + page, file=sys.stderr)
        return False
    else:
        if "Strict-Transport-Security" in r.headers:
            return True
        else:
            return False

def get_tls(page):
    new_page = page + ":443"
    cmd = ["openssl", "s_client", "TLS", "-connect", new_page]
    tls = []
    # tls 1.0
    cmd[2] = "-tls1"
    if len(run_cmd(cmd)) != 0: tls.append("TLSv1.0")
    # tls 1.1
    cmd[2] = "-tls1_1"
    if len(run_cmd(cmd)) != 0: tls.append("TLSv1.1")
    # tls 1.2
    cmd[2] = "-tls1_2"
    if len(run_cmd(cmd)) != 0: tls.append("TLSv1.2")
    # tls 1.3
    cmd[2] = "-tls1_3"
    if len(run_cmd(cmd)) != 0: tls.append("TLSv1.3")
    return tls

def get_root_ca(page):
    new_page = page + ":443"
    cmd = ["openssl", "s_client", "-connect", new_page]
    res = run_cmd(cmd)
    
    if len(res) > 0:
        #print(res)
        a = res.split("---\nServer certificate")
        #print(a[0])
        b = a[0].split("---\nCertificate chain")
        #print(b)
        c = b[1].split("\n")
        #print(c)
        d = c[-2].split("O = ")
        #print(d)
        e = d[1].split(",")
        #print(e)
        f = e[0].strip()
        #print(f)
        return f
    else:
        return None

def get_rdns(ip4):
    rdns = []
    for ip in ip4:
        addr = reversename.from_address(ip)
        ans = resolver.query(addr,"PTR")
        for rr in ans:
            rdns.append(str(rr))
    return rdns

def get_rtt(ip4):
    rtt = []
    for ip in ip4:
        for port in [80, 443, 22]:
            host = socket.gethostbyname(ip)
            before = time.perf_counter()
            try:
                s = socket.create_connection((host, port), timeout=2)
            except socket.timeout:
                continue
            else:
                after = time.perf_counter()
                rtt.append(after-before)
    maxrtt = max(rtt)
    minrtt = min(rtt)
    maxrtt *= 1000
    minrtt *= 1000
    out = [minrtt,maxrtt]
    return out

def get_geo_loc(ip4):
    geolocator = Nominatim(user_agent="geoapiExercises")
    locs = []
    names = []
    with maxminddb.open_database('GeoLite2-City.mmdb') as r:
        for ip in ip4:
            m = r.get(ip)
            locs.append([m["location"]["latitude"], m["location"]["longitude"]])
    # get city, state, country using geopy lib
    for loc in locs:
        pos = str(loc[0]) + "," + str(loc[1])
        pos_name = geolocator.reverse(pos)
        names.append(str(pos_name))

    # removing duplicate names
    name_set = set(names)
    return list(name_set)

user_in = sys.argv[1]
user_out = sys.argv[2]
fill_to_scan(user_in)
scan_sites()
fill_json_out(user_out)