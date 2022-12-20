#!/usr/bin/env python

import xml.etree.ElementTree as ET
import os
import sys
import getopt
import shutil
from jinja2 import Template,Environment,FileSystemLoader

# The list for all the test cases run.
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

hostname = ""
timestamp = ""
section = "global"

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

def generate_one_run(root):

    hostname = root.attrib["hostname"]
    timestamp = root.attrib["timestamp"]
    section = "global"

    for i in root.findall("./properties/property"):
        if i.attrib["name"] == "SECTION":
            section = i.attrib["value"]
            if section == "-no-sections-":
                section = "global"
    
    detail_dir = output_dir + "/details/" + hostname + "/" + timestamp
    
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
    
    #for i in total_cases:
    #    print(i)
    
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


optlist, args = getopt.getopt(sys.argv[1:], 'd:')

if len(args) != 1:
    usage()
    exit(1)

output_dir = sys.path[0]

for o, a in optlist:
    if o == "-d":
        output_dir = a

tree = ET.parse(args[0])
root = tree.getroot()
generate_one_run(root)

