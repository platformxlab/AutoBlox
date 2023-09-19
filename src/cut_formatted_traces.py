import numpy as np
import json

val_trace_dir = "../pure_val_traces/"

    
def store_trace(dir, io_vec):
    f = open(dir, "w")
    for io in io_vec:
        for i in range(0, len(io)):
            io[i] = str(int(io[i]))
        f.write(" ".join(io) + "\n")
    f.flush()
    f.close()

print("Step1, getting raw traces, and calculate bandwidth...")
import os
# the initial datas%


# converted_names = os.listdir("../traces/")
# converted_names = [f"DevTool-{i}" for i in range(23)]
# converted_names += [f"VDI-{i}" for i in range(32)]
# converted_names += [f"MSN-{i}" for i in range(35)]
# converted_names = [f"FINANCIAL-{i}" for i in range(2)]
# converted_names = [f"MLPrep-{i}" for i in range(1)]
# converted_names = [f"FIUHome-{i}" for i in range(1, 22)]
# converted_names = [f"PageRank-{i}" for i in range(0, 1)]
converted_names = [f"RadiusAuth-{i}" for i in range(0, 20)]
# converted_names = ["TPCC-0"]
# converted_names = ["YCSB-0"]
cates = {}
for name in converted_names:
    cat = name.split("-")[0]
    if cat not in cates:
        cates[cat] = []
    cates[cat].append(name)

main_cates = ["RadiusAuth"]

max_tracelength = 100000000
ccount = 0
for cat in main_cates:
    ccount += 1
    print(f"Progress:{ccount}/{len(cates)}")
    trace_dat = {}
    current_converted_names = cates[cat]
    for fname in current_converted_names:
        print(fname)
        f = open("../traces/" + fname, "r")
        traces = f.readlines()
        f.close()
        print(f"Read Finished. Length={len(traces)}")
        if len(traces) > max_tracelength:
            traces = traces[0 : max_tracelength]
        # calculate estimated bandwidth
        bytes_transferred_read = 0
        bytes_transferred_write = 0
        time_start = 0
        for i in range(0, len(traces)):
            traces[i] = traces[i].split(" ")
            for j in range(0, len(traces[i])):
                traces[i][j] = float(traces[i][j])
            if traces[i][4] == 0:
                bytes_transferred_write += traces[i][3] * 512
            else:
                bytes_transferred_read += traces[i][3] * 512
            if i == 0:
                time_start = traces[i][0]
            time_end = traces[i][0]
        estimated_read_bandwidth = 1024 * bytes_transferred_read / (time_end - time_start)
        estimated_write_bandwidth = 1024 * bytes_transferred_write / (time_end - time_start)
        print(f"Bandwidth Estimation: {fname} Read [{estimated_read_bandwidth} MB/s] Write [{estimated_write_bandwidth} MB/s]")
        trace_dat[fname] = traces
    print("Step1 finished.")
    print("Step2, seperating trace with device number")
    training_set_maxnum = 0
    training_dat = {}
    validation_dat = {}
    max_exec_count = 2000000000
    min_exec_count = 0
    catenum = {}
    val_catenum = {}
    for name in trace_dat:
        cat = name.split("-")[0]
        if cat not in catenum:
            catenum[cat] = 0
            val_catenum[cat] = 0
    divided_trace_dat = {}
    for name in trace_dat:
        # divided_trace_dat[name + "-0"] = trace_dat[name]
        ssd_dict = {}
        for line in trace_dat[name]:
            ssd = line[1]
            if ssd not in ssd_dict:
                ssd_dict[ssd] = []
            ssd_dict[ssd].append(line)
        for ssd in ssd_dict:
            divided_trace_dat[name + "-" + str(int(ssd))] = ssd_dict[ssd]
    del trace_dat
    trace_dat = divided_trace_dat
    # calculate bandwidth for each SSD
    for tracename in trace_dat:
        trace = trace_dat[tracename]
        bytes_transferred_read = 0
        bytes_transferred_write = 0
        time_start = trace[0][0]
        time_end = trace[-1][0]
        for req in trace:
            if req[-1] == 0:
                bytes_transferred_write += req[3] * 512
            else:
                bytes_transferred_read += req[3] * 512
        estimated_read_bandwidth = 0
        estimated_write_bandwidth = 0
        if time_end != time_start:
            estimated_read_bandwidth = 1024 * bytes_transferred_read / (time_end - time_start)
            estimated_write_bandwidth = 1024 * bytes_transferred_write / (time_end - time_start)
        print(f"Bandwidth Estimation for {tracename}: {fname} Read [{estimated_read_bandwidth} MB/s] Write [{estimated_write_bandwidth} MB/s] \n Total Requests {len(trace)} TimeSpan {time_end - time_start}")
    print("Step3 sorting trace with time in each category....")
    cat_tracedat = {}
    for name in trace_dat:
        cat = name.split("-")[0]
        dn = int(name.split("-")[-1])
        traceid = int(name.split("-")[-2])
        if cat not in cat_tracedat:
            cat_tracedat[cat] = {}
        if dn not in cat_tracedat[cat]:
            cat_tracedat[cat][dn] = []
        insert_position = -1
        for i in range(len(cat_tracedat[cat][dn])):
            if cat_tracedat[cat][dn][i][0] > traceid:
                insert_position = i
                break
        if insert_position == -1:
            cat_tracedat[cat][dn].append([traceid, trace_dat[name]])
        else:
            cat_tracedat[cat][dn].insert(insert_position, [traceid, trace_dat[name]])
    # adjust timestamp
    print("Step4 deviding trace with capacity....")
    del trace_dat
    # then, devide by capacity
    final_tracedat = {}
    ffinal_tracedat = {}
    # cap = 256 * (2**30) / 512
    length_threshold = 10000000
    length_threshold_min = 10000
    page_sector = 8
    from math import ceil
    for cat in cat_tracedat:
        print("Segment of category " + cat + ": ")
        if cat not in final_tracedat:
            final_tracedat[cat] = {}
            ffinal_tracedat[cat] = {}
        for dn in cat_tracedat[cat]:
            if dn not in final_tracedat[cat]:
                final_tracedat[cat][dn] = []
                ffinal_tracedat[cat][dn] = []
            prev_average = -1
            prev_end = -1
            for i in range(len(cat_tracedat[cat][dn])):
                print("segment of dn:" + str(dn) + ", traceid:" + str(cat_tracedat[cat][dn][i][0]))
                segment = cat_tracedat[cat][dn][i]
                # concat timestamp with moving average gap between reqeusts 
                if i == 0:
                    final_tracedat[cat][dn].append(segment[1])
                    prev_average = int((final_tracedat[cat][dn][0][-1][0] - final_tracedat[cat][dn][0][0][0]) / len(final_tracedat[cat][dn][0]))
                    prev_end = final_tracedat[cat][dn][0][-1][0]
                    continue
                final_tracedat[cat][dn].append(segment[1])
                origin_begin = final_tracedat[cat][dn][i][0][0]
                for k in range(len(final_tracedat[cat][dn][i])):
                    final_tracedat[cat][dn][i][k][0] = final_tracedat[cat][dn][i][k][0] - origin_begin + prev_average + prev_end
                prev_average = int((final_tracedat[cat][dn][i][-1][0] - final_tracedat[cat][dn][i][0][0]) / len(final_tracedat[cat][dn][i]))
                prev_end = final_tracedat[cat][dn][i][-1][0]
        for dn in final_tracedat[cat]:
            for trace in final_tracedat[cat][dn]:
                ffinal_tracedat[cat][dn] += trace
            # verify timestamp
            prev = -1
            for tracetime in ffinal_tracedat[cat][dn]:
                cur = tracetime[0]
                if cur < prev:
                    print("ERROR: TIMESTAMP ERROR IN TRACE CONVERSION.")
                    exit(0)
                prev = cur
    # print("Step2 finished.")
    print("Step5 store traces and configurations....")
    for key1 in ffinal_tracedat:
        for key2 in ffinal_tracedat[key1]:
            print(val_trace_dir + str(key1) + "-" + str(key2) + "-0" )
            store_trace(val_trace_dir + str(key1) + "-" + str(key2) + "-0" , ffinal_tracedat[key1][key2])
                # for i in range(len(final_tracedat[key1][key2][key3])):
                #     store_trace(val_trace_dir + str(key1) + "-" + str(key2) + "-" + str(key3) + "-" + str(i), final_tracedat[key1][key2][key3][i])
    # for trace in validation_dat:
    #     store_trace(val_trace_dir + trace, validation_dat[trace])
    # for trace in training_dat:
    #     store_trace(val_trace_dir + trace, training_dat[trace])
    del final_tracedat
    del ffinal_tracedat

print("Steps finished")
