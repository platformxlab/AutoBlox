import numpy as np
import json

val_trace_dir = "../val_traces/"
train_trace_dir = "../train_traces/"
test_trace_dir = "../test_traces/"


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

# existing_traces = ["TPCETest-10-0", "TPCETest-11-0", "TPCETest-12-0", "TPCETest-13-0", "TPCETest-14-0", "TPCETest-15-0", "TPCETest-16-0", "TPCETest-17-0"]


# each warmup trace should fill in this cache.
# max_dram_size_in_sector = 3.2 * 1024 * 1024 * 1024 / 512
# each trace should be smaller than this length.
min_tracelength = 10000000
min_warmup_trace = 1000000
train_ratio = 0.7
test_ratio = 0.1
val_ratio = 0.2

final_traces = {}
converted_traces = []
page_sector = 8
from math import ceil

# converted_names_list = os.listdir("../pure_val_traces/")
# converted_names_list = [f"YCSB-0-0"]
# converted_names_list = [f"MapReduce-{i}-0" for i in range(0,5)]
# converted_names_list = [f"AdspayLoad-0-0"]
# converted_names_list = [f"CloudStorage-{i}-0" for i in range(0,33)]
# converted_names_list = [f"WebSearch-{i}-0" for i in range(0,3)]
# converted_names_list = [f"LiveMapsBackEnd-{i}-0" for i in range(0,2)]
# converted_names_list = [f"DevTool-{i}-0" for i in range(0,2)]
# converted_names_list = [f"MSN-{i}-0" for i in range(0,2)]
# converted_names_list = [f"VDI-{i}-0" for i in range(0,7)]
# converted_names_list = [f"PageRank-{i}-0" for i in range(1)]
converted_names_list = [f"RadiusAuth-{i}-0" for i in range(1)]
# existing_mainkeys = []
# for n in ["../val_traces/","../test_traces/","../train_traces/"]:
#     existing_names = os.listdir(n)
#     for name in existing_names:
#         main_key = "-".join(name.split("-")[0:-1])
#         if main_key not in existing_mainkeys:
#             existing_mainkeys.append(main_key)




SECOND2NANOSECOND = 1000000000

duration_cut = 300 * SECOND2NANOSECOND

for fname in converted_names_list:
    print(fname)
    if fname not in os.listdir("../pure_val_traces/"):
        continue
    if len(fname.split("-")) != 3:
        continue
    main_name = fname
    new_traces = []
    f = open("../pure_val_traces/" + fname, "r")
    print("Extracted. Converting....")
    count = 0
    lines = f.readlines()
    address_dic = {}
    total_footprint = 0
    # cut the trace based on duration count, or footprint
    trace_endpoints = [0]
    if fname.split("-")[0] in ["YCSB","LiveMapsBackEnd"]:
        previous_section_endtime = int(lines[0].split(" ")[0])
        for i in range(len(lines)):
            cur_time = int(lines[i].split(" ")[0])
            if cur_time - previous_section_endtime > duration_cut:
                trace_endpoints.append(i)
                previous_section_endtime = cur_time
    if fname.split("-")[0] in ["AdspayLoad"]:
        previous_section_endtime = int(lines[0].split(" ")[0])
        for i in range(len(lines)):
            cur_time = int(lines[i].split(" ")[0])
            if cur_time - previous_section_endtime > 20000 * SECOND2NANOSECOND:
                trace_endpoints.append(i)
                previous_section_endtime = cur_time
    if fname.split("-")[0] in ["VDI"]:
        previous_section_endtime = int(lines[0].split(" ")[0])
        for i in range(len(lines)):
            cur_time = int(lines[i].split(" ")[0])
            if cur_time - previous_section_endtime > 6000 * SECOND2NANOSECOND:
                trace_endpoints.append(i)
                previous_section_endtime = cur_time
    if fname.split("-")[0] in ["PageRank"]:
        previous_section_endtime = int(lines[0].split(" ")[0])
        for i in range(len(lines)):
            cur_time = int(lines[i].split(" ")[0])
            if cur_time - previous_section_endtime > 300 * SECOND2NANOSECOND:
                trace_endpoints.append(i)
                previous_section_endtime = cur_time
    if fname.split("-")[0] in ["MSN", "DevTools", "FIUHome"]:
        trace_seg = 2000000
        for i in range(len(lines)):
            if i % trace_seg == 0 and i != 0:
                trace_endpoints.append(i)
    if fname.split("-")[0] in ["RadiusAuth"]:
        previous_section_endtime = int(lines[0].split(" ")[0])
        for i in range(len(lines)):
            cur_time = int(lines[i].split(" ")[0])
            if cur_time - previous_section_endtime > 10000 * SECOND2NANOSECOND:
                trace_endpoints.append(i)
                previous_section_endtime = cur_time
    if fname.split("-")[0] in ["MLPrep"]:
        previous_section_endtime = int(lines[0].split(" ")[0])
        for i in range(len(lines)):
            cur_time = int(lines[i].split(" ")[0])
            if cur_time - previous_section_endtime > 1000 * SECOND2NANOSECOND:
                trace_endpoints.append(i)
                previous_section_endtime = cur_time
    if len(trace_endpoints) > 1:
        trace_endpoints[-1] = len(lines)
    else:
        trace_endpoints.append(len(lines))
    # separate different trace parts
    print(f"splitted trace:{trace_endpoints}")
    splitted_traces = []
    for i in range(len(trace_endpoints) - 1):
        splitted_traces.append(lines[trace_endpoints[i] : trace_endpoints[i + 1]])
    # move time stamp
    maxthpt = 0
    for i in range(len(splitted_traces)):
        address_dic = {}
        lines = splitted_traces[i]
        duration = float(int(lines[-1].split(" ")[0]) - int(lines[0].split(" ")[0])) / 1000000000
        print(f"cutted duration:{duration}, length={len(lines)}\n")
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
        newfname = (fname + "-" + str(i))
        if total_transfered / (duration * 1024 * 1024) > maxthpt:
            maxthpt = total_transfered / (duration * 1024 * 1024)
        print(f"Trace: {newfname}, duration: {duration} s, length: {total_count}, total footprint = {total_footprint} B, bandwidth = {total_transfered / (duration * 1024 * 1024)} MB/s, max:{maxthpt}\n")
        store_string_trace(val_trace_dir + str(fname) + "-" + str(i) , lines)
