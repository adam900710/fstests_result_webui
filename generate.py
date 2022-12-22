#!/usr/bin/env python

import xml.etree.ElementTree as ET
import os
import sys
import getopt
import shutil
from jinja2 import Template,Environment,FileSystemLoader
from datetime import datetime

# The list for all the test cases in one run. (specified by the xml)
# The content of each list member is a dict:
#  "name"       test case name, e.g "btrfs/001"
#  "result"     test result, "pass"|"fail"|"notrun"
#  "time"       test execution time, e.g. 10
#  "messages"   for skipped case only, indicates the reason.
#  "has_out"    if the test case has .out.bad file
#  "has_dmesg"  if the test case has .dmesg file
passed_cases = []
failed_cases = []
skipped_cases = []
total_cases = []

# The dict of all the history runs
#
# The dict has the following keys:
#   hostname + "-" + section: dict
#
# The dict would be something like:
#   timestamp: [{"passed": number, "failed": number, "skipped": number}]
#
# This is mostly to aggregate the runs into their configs and timestamps.
history_runs = {}

# Each element would be a dict:
# "config":     hostname + "-" + section
# "timestamp":  the timestamp of the run
# "passed":     passed test case
# "failed":     failed test case
# "skipped":    skipped test case
plain_runs = []

def write_into_path(path, content):
    try:
        os.mkdir(os.path.dirname(path))
    except FileExistsError:
        pass

    f = open(path, "w")
    f.write(content)
    f.close()

def usage():
    print("Usage:", file=sys.stderr)
    print(sys.argv[0] + ": <result.xml> [-d <output_dir>]", file=sys.stderr)

def generate_one_run(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    hostname = root.attrib["hostname"]
    timestamp = root.attrib["timestamp"]
    section = "global"

    for i in root.findall("./properties/property"):
        if i.attrib["name"] == "SECTION":
            section = i.attrib["value"]
            if section == "-no-sections-":
                section = "global"
    
    detail_dir = output_dir + "/details/" + hostname + "-" + section + "/" + timestamp 
    
    try:
        os.makedirs(detail_dir)
    except FileExistsError:
        pass
     
    index_path = detail_dir + "/index.html"
    
    for testcase in root.findall("testcase"):
        seqnum = testcase.attrib["name"]
        path = detail_dir + "/" + seqnum
    
        time = testcase.attrib["time"]
    
        failure = testcase.find("failure")
        skipped = testcase.find("skipped")
    
        has_out = False
        has_dmesg = False
        message = ""
    
        for i in testcase.iter('system-out'):
            write_into_path(path + ".out.bad", i.text)
            has_out = True
    
        for i in testcase.iter('system-err'):
            write_into_path(path + ".dmesg", i.text)
            has_dmesg = True
    
        if failure is not None:
            output = "failed"
        elif skipped is not None:
            output = "skipped"
            message = skipped.attrib["message"]
        else:
            output = "pass"
    
        this_case = {
            "name": seqnum,
            "result_str": output,
            "time": time,
            "has_out": has_out,
            "has_dmesg": has_dmesg,
            "message": message
        }
    
        total_cases.append(this_case)
    
        if output == "failed":
            failed_cases.append(this_case)
        elif output == "skipped":
            skipped_cases.append(this_case)
        else:
            passed_cases.append(this_case)
    
    env = Environment(loader=FileSystemLoader('.'))
    one_run_template = env.get_template('one_run.jinja')
    
    f = open(index_path, "w")
    f.write(one_run_template.render(hostname=hostname, section=section,
                                    timestamp=timestamp, passed_cases=passed_cases,
                                    failed_cases=failed_cases,
                                    skipped_cases=skipped_cases))
    f.close()
    try:
        shutil.copy("./style.css", output_dir)
    except shutil.SameFileError:
        pass

    # Copy the xml into detail_dir/result.xml for history checks
    shutil.copy(xml_path, detail_dir + "/result.xml")

def add_one_history_run(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    hostname = root.attrib["hostname"]
    timestamp = root.attrib["timestamp"]
    section = "global"

    for i in root.findall("./properties/property"):
        if i.attrib["name"] == "SECTION":
            section = i.attrib["value"]
            if section == "-no-sections-":
                section = "global"
    config = hostname + "-" + section
    if config not in history_runs:
        history_runs[config] = {}
    if timestamp not in history_runs[config]:
        history_runs[config][timestamp] = []
    tests = int(root.attrib["tests"])
    failed = int(root.attrib["failures"])
    skipped = int(root.attrib["skipped"])
    passed = tests - failed - skipped
    this_run = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
    }
    history_runs[config][timestamp] = this_run

def get_date(one_plain_run):
    return datetime.fromisoformat(one_plain_run["timestamp"])

optlist, args = getopt.getopt(sys.argv[1:], 'd:')

if len(args) != 1:
    usage()
    exit(1)

output_dir = sys.path[0]

for o, a in optlist:
    if o == "-d":
        output_dir = a

generate_one_run(args[0])

for config_path in os.listdir(output_dir + "/details"):
    for timestamp_path in os.listdir(output_dir + "/details/" + config_path):
        add_one_history_run(output_dir + "/details/" + config_path + "/" +\
                            timestamp_path + "/result.xml")


# Make a plain list of all history runs, allowing us to generate the summary
# page
for one_type in history_runs.items():
    config = one_type[0]
    for one_run in one_type[1].items():
        timestamp = one_run[0]
        plain_runs.append({
            "config": config,
            "timestamp": timestamp,
            "passed": one_run[1]["passed"],
            "failed": one_run[1]["failed"],
            "skipped": one_run[1]["skipped"],
            "url": "details/" + config + "/" + timestamp + "/index.html",
        })


plain_runs.sort(reverse=True, key=get_date)
env = Environment(loader=FileSystemLoader('.'))
summary_template = env.get_template('summary.jinja')

f = open(output_dir + "/index.html", "w")
f.write(summary_template.render(runs=plain_runs))
f.close()

shutil.copy("style.css", output_dir)
