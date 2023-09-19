import numpy as np
import json

val_trace_dir = "../val_traces/"


def store_trace(dir, io_vec):
    f = open(dir, "w")
    for io in io_vec:
        for i in range(0, len(io)):
            io[i] = str(int(io[i]))
        f.write(" ".join(io) + "\n")
    f.flush()
    f.close()

def store_string_trace(dir, trace_vec):
    f = open(dir, "w")
    for trace in trace_vec:
        f.write(trace)
    f.flush()
    f.close()

print("Step1, getting raw traces..")
import os
# the initial datas
trace_dat = {}

final_traces = {}
converted_traces = []
page_sector = 8
from math import ceil

converted_names_list = os.listdir(val_trace_dir)

SECOND2NANOSECOND = 1000000000

duration_cut = 1 * SECOND2NANOSECOND

# dictionary for maximum bandwidth, request count in the maximum bandwidth window,  and minimum request count in each window for each workloads
max_bandwidth = {}
for fname in converted_names_list:
    category = fname.split("-")[0]
    if not category in ["RadiusAuth"]:
        continue
    print(fname)
    print(category)
    category = category + fname.split("-")[1]
    if category not in max_bandwidth:
        max_bandwidth[category] = [0.0, 1e10, 1e10]
    f = open(val_trace_dir + fname, "r")
    print("Extracted. Converting....")
    count = 0
    lines = f.readlines()
    address_dic = {}
    total_footprint = 0
    # cut the trace based on duration count, or footprint
    trace_endpoints = [0]
    previous_section_endtime = int(lines[0].split(" ")[0])
    for i in range(len(lines)):
        cur_time = int(lines[i].split(" ")[0])
        if cur_time - previous_section_endtime > duration_cut:
            trace_endpoints.append(i)
            previous_section_endtime = cur_time
    if len(trace_endpoints) > 1:
        trace_endpoints[-1] = len(lines)
    else:
        trace_endpoints.append(len(lines))
    # separate different trace parts
    # print(f"splitted trace:{trace_endpoints}")
    splitted_traces = []
    for i in range(len(trace_endpoints) - 1):
        splitted_traces.append(lines[trace_endpoints[i] : trace_endpoints[i + 1]])
    # move time stamp
    maxthpt = 0
    maxwindow = 1e10
    min_window = 1e10
    piceccount = 0
    all_bandwidth = 0
    for i in range(len(splitted_traces)):
        address_dic = {}
        lines = splitted_traces[i]
        if len(lines) < 100:
            continue
        duration = float(int(lines[-1].split(" ")[0]) - int(lines[0].split(" ")[0])) / 1000000000
        if duration * 1000000000 < 0.8 * duration_cut:
            duration = duration_cut / 1000000000
        # print(f"cutted duration:{duration}, length={len(lines)}\n")
        total_count = len(lines)
        total_footprint = 0
        total_transfered = 0
        start_time = int(lines[0].split(" ")[0])
        for j in range(len(lines)):
            l = lines[j].split(" ")
            l[0] = str(int(l[0]) - start_time)
            lines[j] = " ".join(l)
            if l[2] not in address_dic:
                address_dic[l[2]] = 0
                total_footprint += int(l[3]) * 512
            total_transfered += int(l[3]) * 512
        # print(total_transfered / (duration * 1024 * 1024))
        if total_transfered / (duration * 1024 * 1024) > maxthpt:
            maxthpt = total_transfered / (duration * 1024 * 1024)
            maxwindow = len(splitted_traces[i])
        if len(splitted_traces[i]) < min_window:
            min_window = len(splitted_traces[i])
    print(f"Trace: {fname}, max_bandwidth: {maxthpt} MB/s, {maxwindow} {min_window}\n")
    if maxthpt > max_bandwidth[category][0]:
        max_bandwidth[category][0] = maxthpt
        max_bandwidth[category][1] = maxwindow
    if min_window < max_bandwidth[category][2]:
        max_bandwidth[category][2] = min_window

print("***** Display final results *****:")
for cat in max_bandwidth:
    print(f"Trace: {cat}, max_bandwidth: {max_bandwidth[cat][0]} MB/s, with window length = {max_bandwidth[cat][1]}, min window length = {max_bandwidth[cat][2]}\n")

