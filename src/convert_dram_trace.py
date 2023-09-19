from math import ceil
from collections import OrderedDict

# Input : filename, the file of the dram trace collected from MQSim that need conversion;
# Input : dram_capacity, dram capacity for this trace in bytes;
# Input : page_size, page size in bytes;
# Input : dram_address_begin, start address of this dram part (In case, we need to merge two parts of different drams)
def convert_dram_trace(filename, dram_capacity, page_size, dram_address_begin):
    dram_trace = [] # format of output : TimeStamp, READ/WRITE, PPA(hex. 8 byte per request).
    f = open(filename, "r")
    lines = f.readlines()
    f.close()
    simulated_dram = OrderedDict() # page(4KB) level mapping table for DRAM, LPA -> PPA of DRAM
    ppa_free_list = [address for address in range(0, dram_capacity, page_size)] # free list for PPA
    # lru_dict = {} # LPA -> position in lru_list
    # lru_list = [] # list of LPA in the order of lru at first
    max_capacity = ceil(float(dram_capacity) / page_size)
    i = 0
    hit = 0
    miss = 0
    lru = 0
    for line in lines:
        i = i + 1
        print(f"{i}/{len(lines)} {hit} {miss} {lru}", end="\r")
        line = line.split(" ") #   TimeStamp, READ/WRITE, LPA, Size
        # first, find the dram physical address by LPA 
        # (Should be page by page, so first I should fetch all the pages)
        start_LPA = int(line[2])
        LPA_count = ceil(float(line[3]) / float(page_size))
        LPAs = [start_LPA + i for i in range(LPA_count)]
        for LPA in LPAs:
            if LPA in simulated_dram: # data is already there, only need to read/write it.
                dram_trace += [[line[0], line[1], hex(simulated_dram[LPA])] ]
                PPA = simulated_dram[LPA]
                del simulated_dram[LPA]
                simulated_dram[LPA] = PPA
                # assert(LPA in lru_dict)
                # prev_id = lru_dict[LPA]
                # lru_list.remove(LPA)
                # lru_list.append(LPA)
                # lru_dict[LPA] = len(lru_list) - 1
                hit += 1
            elif len(simulated_dram) < max_capacity:
                PPA = ppa_free_list.pop(0)
                # lru_list.append(LPA)
                # lru_dict[LPA] = len(lru_list) - 1
                simulated_dram[LPA] = PPA
                dram_trace += [[line[0], "WRITE", hex(simulated_dram[LPA])]]
                miss += 1
                if line[1] == "READ":
                    dram_trace += [[line[0], "READ", hex(simulated_dram[LPA])]]
            else: # should allocate a new page to the LPA.
                lru += 1
                victim_lpa = next(iter(simulated_dram))
                # victim_lpa = lru_list.pop(0)
                # assert(victim_lpa in lru_dict)
                freed_PPA = simulated_dram[victim_lpa]
                del simulated_dram[victim_lpa]
                # del lru_dict[victim_lpa]
                # lru_list.append(LPA)
                # lru_dict[LPA] = len(lru_list) - 1
                simulated_dram[LPA] = freed_PPA
                dram_trace += [[line[0], "WRITE", hex(simulated_dram[LPA])]]
                if line[1] == "READ":
                    dram_trace += [[line[0], "READ", hex(simulated_dram[LPA])]]
    return dram_trace

def merge_two_traces_and_convert(dtrace1, dtrace2):
    dram_trace_merged = []
    index1 = 0
    index2 = 0
    while (index1 < len(dtrace1) and index2 < len(dtrace2)):
        if int(dtrace1[index1][0]) <= int(dtrace2[index2][0]):
            dram_trace_merged.append(dtrace1[index1])
            index1 += 1
        else:
            dram_trace_merged.append(dtrace2[index2])
            index2 += 1
        print(f"{index1}/{len(dtrace1)} {index2}/{len(dtrace2)}", end="\r")
    if index1 < len(dtrace1):
        dram_trace_merged += (dtrace1[index1:len(dtrace1)])
    if index2 < len(dtrace2):
        dram_trace_merged += (dtrace2[index2:len(dtrace2)])
    # change the timestamp
    prev_timestamp = int(dram_trace_merged[0][0])
    for i in range(1, len(dram_trace_merged)):
        dram_trace_merged[i][0] = str(int(dram_trace_merged[i][0]) - prev_timestamp)
        prev_timestamp += int(dram_trace_merged[i][0])
        print(f"{i}/{len(dram_trace_merged)}", end="\r")
    return dram_trace_merged

def write_trace(filename, tracelist):
    f = open(filename, "w")
    for traceitem in tracelist:
        f.write(str(traceitem[0]) + " " + str(traceitem[1]) + " " + str(traceitem[2]) + "\n")
    f.close()

def read_trace(filename):
    f = open(filename, "r")
    lines = f.readlines()
    f.close()
    return lines

def write_trace_by_lines(filename, tracelines):
    f = open(filename, "w")
    for line in tracelines:
        f.write(line)
    f.close()

import os

allowed_combinations = {
    "RC3" : "AdspayLoad",
    "KV" : "YCSB",
    "DB" : "TPCC",
    "WS11" : "WebSearch",
    "CS10" : "MapReduce",
    "CS2" : "CloudStorage",
    "MR" : "LiveMapsBackEnd"
}

dram_sizes = {
    "baseline" : [838860800, 268435456],
    "RC3" : [704643072, 402653184],
    "KV" : [704643072, 402653184],
    "DB" : [704643072, 402653184],
    "WS11" : [1040187392, 67108864],
    "CS10" : [436207616, 671088640],
    "CS2" : [973078528, 134217728],
    "MR" : [838860800, 268435456]
}

dram_trace_dir = "../xdb/nvme_mlc/dram_trace"
for name in os.listdir(dram_trace_dir):
    if name.endswith(".cmt"):
        # first, check whether this is the target combination we want  
        conf_name = name.split("_")[0]
        workload_name = name.split("_")[2].split("-")[0]
        if name[0:-14] + ".trace" in os.listdir("/mnt/nvme1n1/daixuan2/"):
            continue
        if "baseline" == conf_name or (conf_name in allowed_combinations and allowed_combinations[conf_name] == workload_name):
            print(f"{conf_name} on {workload_name}....")
            dram_tracename = name[0:-4]
            result = convert_dram_trace("../xdb/nvme_mlc/dram_trace/" + dram_tracename, dram_sizes[conf_name][0], 4096, 0)
            result1 = convert_dram_trace("../xdb/nvme_mlc/dram_trace/" + name, dram_sizes[conf_name][1], 4096, dram_sizes[conf_name][0])
            result_tot = merge_two_traces_and_convert(result, result1)
            write_trace("/mnt/nvme1n1/daixuan2/" + name[0:-14] + ".trace", result_tot)
            del result
            del result1
            del result_tot

