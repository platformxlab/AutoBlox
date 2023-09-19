import sys
import numpy as np
import math
import time
import random
import json
from time import sleep
import xml
from xml.dom.minidom import Document
import os
from batch_evaluation import batch_exec
from evaluate_target_conf import generate_config_workload, save_to_xdb, get_performance_from_xml, evaluate_config_workload, generate_queuetest_config_workload


print ('Number of arguments:', len(sys.argv), 'arguments.')
print ('Argument List:', str(sys.argv))

if len(sys.argv) != 3:
    print("Usage: python3 get_recommended_configurations.py xdb_directory target_workload")
    exit()

# extract recommended configurations from XDB

target_workloads = ["TPCC", "WebSearch", "CloudStorage", "LiveMapsBackEnd", "AdspayLoad", "MapReduce", "YCSB"]
xdb_dire = sys.argv[1]

this_target_workload = sys.argv[2]

# workload informations


configuration_choices = {
    "Execution_Parameter_Set" : {
        "Host_Parameter_Set" : {
            "PCIe_Lane_Bandwidth" : [0.5, 1.0, 2.0, 4.0, 8.0], # ! 1Gb/s for PCIe 3, 1 times greater every next gen, PCIe 6 released in 2021 
            "PCIe_Lane_Count" : [1, 2, 4, 8, 16], # ! 1, 2, 4, 8, 16x Type
            "SATA_Processing_Delay" : [100000, 200000, 300000, 400000, 500000], # ! can tune this for different manufacture techiques
            "Enable_ResponseTime_Logging" : ["false"], # * simulation para                                       ****** Not Tunable
            "ResponseTime_Logging_Period_Length" : [1000000], #  simulation para                                ****** Not Tunable
        },
        "Device_Parameter_Set" : {
            "Seed" : [321], # *  Should be randomly set, currently just stay the same to replay results           ****** Not Tunable
            "Enabled_Preconditioning" : ["true"], # *  Preconditioning set to true to se better performance      ****** Not Tunable
            "Memory_Type" : ["FLASH"], # ? No other for our simulator                                            ****** Not Tunable
            "HostInterface_Type" : ["NVME"], # ! Two Kind of Interfaces Here                                     ****** Not Tunable
            "IO_Queue_Depth" : [4, 8, 16, 32, 64, 128, 256], # Pre-determined for each workload, since this is software parameter
            "Queue_Fetch_Size" : [4, 8, 16, 32, 64, 128, 256], # Pre-determined for each workload, since this is software parameter 
            "Caching_Mechanism" : ["ADVANCED"], # Will add new cache strategy here                               ****** Not Tunable
            "Data_Cache_Sharing_Mode" : ["SHARED"], #                                                            ****** Not Tunable
            "Data_Cache_Capacity" : [838860800 + i * 67108864 for i in range(-11, 4)],
            "Data_Cache_DRAM_Row_Size" : [1024, 2048, 4096, 8192, 16384],
            "Data_Cache_DRAM_Data_Rate" : [100, 200, 400, 800, 1600, 2133, 2400, 2666, 3200], # For bus frequency of 100 MHz, DDR SDRAM 200GT/s
            "Data_Cache_DRAM_Data_Busrt_Size" : [1, 2, 4, 8, 16], # Chip Num
            "Data_Cache_DRAM_tRCD" : [4, 7, 14, 21, 28], # Whether use better DRAM for better performance
            "Data_Cache_DRAM_tCL" : [4, 7, 14, 21, 28], # Whether use better DRAM for better performance
            "Data_Cache_DRAM_tRP" : [4, 7, 14, 21, 28], # Whether use better DRAM for better performance
            "Address_Mapping" : ["PAGE_LEVEL"], # hybrid is buggy                                                ****** Not Tunable
            "Ideal_Mapping_Table" : ["false"], # Should be false to be realistic                                 ****** Not Tunable
            "CMT_Capacity" : [67108864 * i for i in range(1, 9)],
            "CMT_Sharing_Mode" : ["SHARED"], #                                                                   ****** Not Tunable
            "Plane_Allocation_Scheme" : ["CWDP", "CWPD", "CDWP", "CDPW", "CPWD", "CPDW", "WCDP", "WCPD", "WDCP", "WDPC", "WPCD", "WPDC", "DCWP", "DCPW", "DWCP", "DWPC", "DPCW", "DPWC", "PCWD", "PCDW", "PWCD", "PWDC", "PDCW", "PDWC"],
            "Transaction_Scheduling_Policy" : ["PRIORITY_OUT_OF_ORDER"], #                                       ****** Not Tunable
            "Overprovisioning_Ratio" : [0.1, 0.15, 0.2, 0.25, 0.3],
            "GC_Exec_Threshold" : [0.1, 0.15, 0.2, 0.25, 0.3],
            "GC_Block_Selection_Policy" : ["GREEDY", "RGA", "RANDOM", "RANDOM_P", "RANDOM_PP", "FIFO"],
            "Use_Copyback_for_GC" : ["true", "false"],
            "Preemptible_GC_Enabled" : ["true", "false"],
            "GC_Hard_Threshold" : [0.1, 0.15, 0.2, 0.25, 0.3], # should be smaller than GC_Exec
            "Dynamic_Wearleveling_Enabled" : ["true", "false"],
            "Static_Wearleveling_Enabled" : ["true", "false"],
            "Static_Wearleveling_Threshold" : [50, 60, 70, 80, 90, 100], 
            "Preferred_suspend_erase_time_for_read" : [100000, 200000, 300000, 400000, 500000],
            "Preferred_suspend_erase_time_for_write" : [100000, 200000, 300000, 400000, 500000],
            "Preferred_suspend_write_time_for_read" : [100000, 200000, 300000, 400000, 500000],
            "Flash_Channel_Count" : [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32], # most regular channel count
            "Flash_Channel_Width" : [1, 2, 4, 8], # my understanding, how much bandwith for each channel. more search needed.
            "Channel_Transfer_Rate" : [100, 200, 333, 800], #  [200,400,800],
            "Chip_No_Per_Channel" : [1, 2, 3, 4, 5, 6, 7, 8],
            "Flash_Comm_Protocol" : ["NVDDR2"], #                                                               ****** Not Tunable
            "Flash_Parameter_Set" : {
                "Flash_Technology" : ["MLC"],
                # "Flash_Technology" : ["SLC", "MLC", "TLC"], # Seems this should be fixed
                "CMD_Suspension_Support" : ["NONE", "PROGRAM", "PROGRAM_ERASE", "ERASE"],
                "Page_Read_Latency_LSB" : [25000, 50000, 59975, 75000, 100000], # when tuning these parameters, we use the average of L/C/M SB
                "Page_Read_Latency_CSB" : [0, 25000, 50000, 75000, 100000],
                "Page_Read_Latency_MSB" : [25000, 50000, 75000, 100000, 104956],
                "Page_Program_Latency_LSB" : [82062, 250000, 500000, 750000, 1000000],
                "Page_Program_Latency_CSB" : [0, 250000, 500000, 750000, 1000000],
                "Page_Program_Latency_MSB" : [250000, 500000, 750000, 1000000, 1250000, 1500000, 1750000, 2000000, 2250000],
                "Block_Erase_Latency" : [3000000, 3800000],
                "Block_PR_Cycles_Limit" : [10000, 20000, 30000, 40000, 50000],
                "Suspend_Erase_Time" : [700000, 800000, 900000, 1000000, 1100000],
                "Suspend_Program_time" : [60000, 70000, 80000, 90000, 100000],
                "Die_No_Per_Chip" : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
                "Plane_No_Per_Die" : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
                "Block_No_Per_Plane" : [128, 256, 384, 512, 640, 768, 896, 1024],
                "Page_No_Per_Block" : [128, 256, 384, 512, 640, 768, 896, 1024],
                "Page_Capacity" : [4096],    #  Temporarily not tunable, since the page capacity relate to other flash parameters(L/C/M SB latency) and the relationship is hard to model without industry insights                                                               
                "Page_Metadat_Capacity" : [224, 448, 672, 896, 1120],
            },
        }
    }
}

global tunable_configuration_names
tunable_configuration_names = []
tunable_configuration_normalizers = []
numericals = {} # store the configuration name 
categorical = {}
booleans = {}
for key in configuration_choices:
    for key1 in configuration_choices[key]:
        for key2 in configuration_choices[key][key1]:
            if key2 != "Flash_Parameter_Set":
                if len(configuration_choices[key][key1][key2]) > 1:
                    tunable_configuration_names.append(key2)
                    tunable_configuration_normalizers.append(configuration_choices[key][key1][key2])
                    if configuration_choices[key][key1][key2][0] == "true" or configuration_choices[key][key1][key2][0] == "false":
                        booleans[key2] = configuration_choices[key][key1][key2]
                    else:
                        isnum = (type(configuration_choices[key][key1][key2][0]) == type(1)) or (type(configuration_choices[key][key1][key2][0]) == type(1.1))
                        if isnum:
                            numericals[key2] = configuration_choices[key][key1][key2]
                        else:
                            categorical[key2] = configuration_choices[key][key1][key2]
            else:
                for key3 in configuration_choices[key][key1][key2]:
                    if len(configuration_choices[key][key1][key2][key3]) > 1:
                        tunable_configuration_names.append(key3)
                        tunable_configuration_normalizers.append(configuration_choices[key][key1][key2][key3])
                        if configuration_choices[key][key1][key2][key3][0] == "true" or configuration_choices[key][key1][key2][key3][0] == "false":
                            booleans[key3] = configuration_choices[key][key1][key2][key3]
                        else:
                            isnum = (type(configuration_choices[key][key1][key2][key3][0]) == type(1)) or (type(configuration_choices[key][key1][key2][key3][0]) == type(1.1))
                            if isnum:
                                numericals[key3] = configuration_choices[key][key1][key2][key3]
                            else:
                                categorical[key3] = configuration_choices[key][key1][key2][key3]



# Turn a configuration file into a configuration vector
# the configuration values are in the order of tunable_configuration_names
def decode_configuration(conf_name):
    # first, get all the tunable values
    try:
        DOMTree = xml.dom.minidom.parse(conf_name)
    except:
        print(f"evaluating configuration {conf_name} failed")
        print("ERROR: Configuration File Not Found")
        return None
    collection = DOMTree.documentElement
    results = collection
    host_results = results.getElementsByTagName("Host_Parameter_Set")[0]
    device_results = results.getElementsByTagName("Device_Parameter_Set")[0]
    flash_parameters = device_results.getElementsByTagName("Flash_Parameter_Set")[0]
    # Get all the parameters in "tunable_configuration_names"
    result_configurations = [-1 for item in tunable_configuration_names]
    # configuration_choices["Execution_Parameter_Set"]["Host_Parameter_Set"]
    for key in configuration_choices["Execution_Parameter_Set"]["Host_Parameter_Set"]:
        if key in tunable_configuration_names:
            result = (host_results.getElementsByTagName(key)[0]).childNodes[0].data
            if key in numericals:
                if type(numericals[key][0]) == type(0.1):
                    result = float(result)
                else:
                    result = int(result)
            result_configurations[tunable_configuration_names.index(key)] = result
    for key in configuration_choices["Execution_Parameter_Set"]["Device_Parameter_Set"]:
        if key in tunable_configuration_names:
            result = (device_results.getElementsByTagName(key)[0]).childNodes[0].data
            if key in numericals:
                if type(numericals[key][0]) == type(0.1):
                    result = float(result)
                else:
                    result = int(result)
            result_configurations[tunable_configuration_names.index(key)] = result
    for key in configuration_choices["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"]:
        if key in tunable_configuration_names:
            result = (flash_parameters.getElementsByTagName(key)[0]).childNodes[0].data
            if key in numericals:
                if type(numericals[key][0]) == type(0.1):
                    result = float(result)
                else:
                    result = int(result)
            result_configurations[tunable_configuration_names.index(key)] = result
    # check whether all the result_configurations are filled
    for k in result_configurations:
        if k == -1:
            print("ERROR! Unfilled result configuration!")
            print(result_configurations)
            print(tunable_configuration_names)
            exit(1)
    return result_configurations

# this file is for inspection of how each configuration evolveduring the Training Process
# import find_best_conf
# from find_best_conf import update_xdb, geo_mean
# from find_best_conf import tunable_configuration_names, explored_configurations, xdbTable, baseline_conf, target_workload

def geo_mean(lis):
    mul = 1
    for i in lis:
        mul *= i
    mul = mul ** (1 / len(lis))
    return mul

def calculate_grade(xdbTable, confid, workload_cat):
    cur_table = xdbTable[confid]
    baseline_table = xdbTable["0"]
    results = {}
    latency_throughput_results = {}
    for cat in cur_table:
        perf_improves = []
        if cat not in baseline_table:
            return -math.inf
        for trace in cur_table[cat]:
            if trace not in baseline_table[cat] or trace == "HYPER":
                continue
            else:
                perf_improves.append([baseline_table[cat][trace][0] / cur_table[cat][trace][0], cur_table[cat][trace][1] / baseline_table[cat][trace][1]])
                break
        if len(perf_improves) == 0:
            results[cat] = -math.inf
            latency_throughput_results[cat] = [-1, -1]
        else:
            lats = []
            thpts = []
            for k in perf_improves:
                lats.append(k[0])
                thpts.append(k[1])
            results[cat] = (1 - alpha) * math.log(geo_mean(lats)) + alpha * math.log(geo_mean(thpts))
            latency_throughput_results[cat] = [geo_mean(lats), geo_mean(thpts)]
    target_grade = 0
    non_target_grade = 0
    non_target_performances = [1, 1]
    non_target_count = 0
    for cat in results:
        if results[cat] == -math.inf:
            return -math.inf
        elif cat == workload_cat:
            target_grade += results[cat]
        else:
            non_target_grade += results[cat]
            non_target_count += 1
            non_target_performances[0] *= latency_throughput_results[cat][0]
            non_target_performances[1] *= latency_throughput_results[cat][1]
    if non_target_count > 0:
        non_target_performances[0] = non_target_performances[0] ** (1 / non_target_count)
        non_target_performances[1] = non_target_performances[1] ** (1 / non_target_count)
    return [(1 - beta) * target_grade + beta * non_target_grade / non_target_count, target_grade, non_target_performances]



# global variables
# xdbTable_file
# conf_file
# calculate_grade()
# 
def update_xdb(xdbTable, explored_configurations, configuration_updates, xdbTable_updates, workload_cat, xdbTable_file, conf_file, table=False, confs=False):
    print("Update XDB!")
    print(f"read {xdbTable_file}")
    f = open(xdbTable_file, "r")
    xdbTable = json.loads(f.read())
    f.close()
    print(f"read {conf_file}")
    f = open(conf_file, "r")
    explored_configurations = json.loads(f.read())
    f.close()
    print(f"Updating...")
    if table:
        for confid in xdbTable_updates:
            if "INVALID" == xdbTable_updates[confid]:
                xdbTable[confid] = "INVALID"
            elif confid not in xdbTable:
                xdbTable[confid] = xdbTable_updates[confid]
                grade = calculate_grade(xdbTable, confid, workload_cat)
                xdbTable[confid][workload_cat]["HYPER"] = [alpha, beta, grade] 
                print(f"Update Proposed Configuration, Average Perf Improvement {math.exp(grade[1])},  Grade Improvement {math.exp(grade[0])}")
            else:
                for key in xdbTable_updates[confid]:
                    if key not in xdbTable[confid]:
                        xdbTable[confid][key] = xdbTable_updates[confid][key]
                    else:
                        for tracename in xdbTable_updates[confid][key]:
                            xdbTable[confid][key][tracename] = xdbTable_updates[confid][key][tracename]
                grade = calculate_grade(xdbTable, confid, workload_cat)
                xdbTable[confid][workload_cat]["HYPER"] = [alpha, beta, grade] 
                print(f"Update Proposed Configuration, Average Perf Improvement {math.exp(grade[1])},  Grade Improvement {math.exp(grade[0])}")
        f = open(xdbTable_file, "w")
        f.write(json.dumps(xdbTable))
        f.close()
        xdbTable_updates = {}
    if confs:
        for c in configuration_updates:
            if c not in explored_configurations:
                explored_configurations.append(c)
        f = open(conf_file, "w")
        f.write(json.dumps(explored_configurations))
        f.close()
        print(explored_configurations)
        configuration_updates = []
    print("Update Finished!")
    return xdbTable, explored_configurations

# show how is the performance and configuration different from the baseline configuration
def show_configuration_detail(confid, workload_cat, explored_configurations, xdbTable, max_grade, max_id, conv_count, equal_grades):
    print(f"Probing detail of configuration {confid} for target workload {workload_cat}")
    if int(confid) == 0:
        print("This is baseline configuration.")
        return None, None, max_grade, max_id, conv_count, equal_grades, None, None
    if str(confid) not in xdbTable:
        print("This config does not exist")
        return None, None, max_grade, max_id, conv_count, equal_grades, None, None
    cur_table = xdbTable[str(confid)]
    baseline_table = xdbTable["0"]
    # cat -> [latency improve, throughput improve, [traces performed]]
    results = {}
    hyper = cur_table[workload_cat]["HYPER"]
    for cat in cur_table:
        perf_improves = []
        traces_performed = []
        if cat not in baseline_table:
            continue
        for trace in cur_table[cat]:
            if trace not in baseline_table[cat] or trace == "HYPER":
                continue
            else:
                traces_performed.append(trace)
                perf_improves.append([baseline_table[cat][trace][0] / cur_table[cat][trace][0], cur_table[cat][trace][1] / baseline_table[cat][trace][1]])
                break
        if len(perf_improves) == 0:
            continue
        else:
            lats = []
            thpts = []
            for k in perf_improves:
                lats.append(k[0])
                thpts.append(k[1])
            results[cat] = [geo_mean(lats), geo_mean(thpts), traces_performed]
    # [parameter name, origin value, new_value]
    changed_parameters_and_value = []
    cur_vec = explored_configurations[int(confid)]
    base_vec = explored_configurations[0]
    for i in range(len(tunable_configuration_names)):
        if cur_vec[i] != base_vec[i]:
            changed_parameters_and_value.append([tunable_configuration_names[i], base_vec[i], cur_vec[i]])
    # print out the configuration
    print(f"**** Valid Configuration {confid} ****")
    print(hyper[2][0])
    grade = float(hyper[2][0])
    if grade > max_grade * 1.01:
        max_grade = grade
        max_id = confid
        new_eq = []
        for g, cid in equal_grades:
            if g > max_grade * 0.99 and g <= max_grade * 1.01:
                new_eq.append([g, cid])
        equal_grades = new_eq
        conv_count = 0
    else:
        conv_count += 1
    if grade > max_grade * 0.99 and grade <= max_grade * 1.01:
        equal_grades.append([grade, confid])
    print(f"Current Max Grade {max_id}, Conv Counter {conv_count}, euqal_cand {len(equal_grades)}, grade range {max_grade * 0.99} - {max_grade * 1.01}")
    print(f"\nPerformance Result Targeting {workload_cat}:")
    for cat in results:
        if cat == workload_cat:
            print(f"** Latency {results[cat][0]} Throughput {results[cat][1]} Performed on {results[cat][2]}")
        else:
            print(f"Latency {results[cat][0]} Throughput {results[cat][1]} Performed on {results[cat][2]}")
    print(f"\nTuned Parameters:")
    # calculate non-target results
    non_target_res = hyper[2][2]
    for item in changed_parameters_and_value:
        print(f"{item[0]} : {item[1]} -> {item[2]}")
    return results, changed_parameters_and_value, max_grade, max_id, conv_count, equal_grades, grade, non_target_res

# get 7 recommended configuration list (10 candidates)

# traces_directory = "../training_traces/"
# configuration_directory = xdb_name + "configurations/"
explored_configuration_file = "confs.json"
xdbTable_name = "xdbTable.json"
parallel_lock_file_name = "lock"

# target_workload
recommended_configuration_candidates = {}

# item[0] is the grade to be compared
def insertion_sort_insert_id(reclist, item):
    i = 0
    while i < len(reclist):
        if reclist[i][0] < item[0]:
            break
        i = i + 1
    return i

for target_workload in target_workloads:
    if this_target_workload != "ALL" and this_target_workload != target_workload:
        continue
    for order_str in ["1"]:
        xdb_name = xdb_dire + f"/nvme_mlc_{target_workload}_{order_str}/"
        # baseline configuration metadata
        baseline_conf_name = xdb_name + "configurations/0.xml"
        baseline_conf = decode_configuration(baseline_conf_name)
        xdbTable_file = xdb_name + xdbTable_name
        conf_file = xdb_name + explored_configuration_file
        xdbTable = {}
        explored_configurations = []
        xdbTable, explored_configurations = update_xdb(xdbTable, explored_configurations, [baseline_conf], {}, target_workload, xdbTable_file, conf_file, True, True)
        max_grade = 0
        max_id = 0
        conv_count = 0
        equal_grades = []
        origin_candidates_list = []
        ignore_candidates_list = []
        for i in range(len(explored_configurations)):
            results, changed_parameters_and_value, max_grade, max_id, conv_count, equal_grades, grade, non_target_res = show_configuration_detail(i, target_workload, explored_configurations, xdbTable, max_grade, max_id, conv_count, equal_grades)
            #TODO may have to change this threshold
            if not results:
                print("This is baseline conf")
                continue
            ignore_candidates_list.insert(insertion_sort_insert_id(ignore_candidates_list, [grade, i, results]), [grade, i, results])
            if non_target_res[0] < 0.99 or non_target_res[1] < 0.99:
                continue
            origin_candidates_list.insert(insertion_sort_insert_id(origin_candidates_list, [grade, i, results]), [grade, i, results])
        recommended_configuration_candidates[target_workload] = {}
        recommended_configuration_candidates[target_workload]["ignore"] = ignore_candidates_list
        recommended_configuration_candidates[target_workload]["origin"] = origin_candidates_list
        # for i in range(len(origin_candidates_list)):
        #     print(origin_candidates_list[i][0])

# assemble the pre-evaluation table 1
# evaluate the configurations, check the power constraints
# make recommendations

pre_eval_table_file = "../reproduced_dat/pre_eval_table.txt"

f = open(pre_eval_table_file, "w")
f.write(" ,")
for target_workload in target_workloads:
    f.write(f" {target_workload},")
f.write("\n")
for target_workload in target_workloads:
    f.write(f"{target_workload},")
    for target_workload1 in target_workloads:
        if target_workload not in recommended_configuration_candidates or target_workload1 not in recommended_configuration_candidates[target_workload]["origin"][0][2]:
            f.write(f"x,")
            continue
        itm1 = recommended_configuration_candidates[target_workload]["origin"][0][2][target_workload1][0]
        itm2 = recommended_configuration_candidates[target_workload]["origin"][0][2][target_workload1][1]
        f.write(f"{itm1}/{itm2},")
    f.write("\n")
f.write("\n")
f.close()

# add profiling data

if this_target_workload == "TPCC" or this_target_workload == "ALL":
    print("generating learning profiling....")
    skipped_parameters_for_this_exp = ["IO_Queue_Depth", "Queue_Fetch_Size", "Block_Erase_Latency", "Page_Program_Latency_MSB", "Page_Program_Latency_CSB","Page_Program_Latency_LSB", "Page_Read_Latency_MSB", "Page_Read_Latency_CSB", "Page_Read_Latency_LSB"]
    names =  tunable_configuration_names
    for n in skipped_parameters_for_this_exp:
        names.remove(n)
    result = [names, [[[]], [[]]], []]
    for order_str in [ "1", "0"]:
        xdb_name = xdb_dire + f"/nvme_mlc_TPCC_{order_str}/"
        time_file = open(xdb_name + f"Training_TPCC.log", "r")
        times = [0]
        current_time = 0
        current_conf = 1
        lines = time_file.readlines()
        for i in range(len(lines)):
            line = lines[i].split(" ")
            current_time += float(line[1]) + float(line[2])
            if int(line[3]) == current_conf:
                times.append(current_time / 3600)
                current_conf += 1
            elif int(line[3]) > current_conf:
                print("DEBUG: There is an erroro in the training profile!")
                exit()
        result[2].append(times)
        # first profile configuration file and normalize it
        explored_configuration_file = "confs.json"
        conf_file = xdb_name + explored_configuration_file
        f = open(conf_file, "r")
        explored_configurations = json.loads(f.read())
        f.close()
        # normalize
        normalized_confs = []
        for conf in explored_configurations:
            for i in range(len(conf)):
                # print(conf[i])
                # print(tunable_configuration_normalizers[i])
                conf[i] = float(tunable_configuration_normalizers[i].index(conf[i])) / float(len(tunable_configuration_normalizers[i]))
                # print(conf[i])
            normalized_confs.append(conf)
        profile = {}
        for i in range(len(tunable_configuration_names)):
            if tunable_configuration_names[i] in skipped_parameters_for_this_exp:
                continue
            tmp = []
            for j in range(len(normalized_confs)):
                tmp.append(normalized_confs[j][i])
            profile[tunable_configuration_names[i]] = tmp
        result[1][1 - int(order_str)].append(profile)
        
        

    import json
    f = open("../reproduced_dat/learning_profile.dat", "w")
    f.write(json.dumps(result))
    f.close()
else:
    print("Not generating learning profile, please use ALL or TPCC as workload to generate learning profile.")

        


# add learning time data
labelmapping = {"CloudStorage":"CS",
                "MapReduce":"MR",
                "TPCC":"DB",
                "YCSB":"KV",
                "LiveMapsBackEnd":"LM",
                "AdspayLoad":"RC",
                "WebSearch":"WS"}
    
dict_cat_tuningtime_order = {}
dict_cat_tuningtime_noorder = {}
for target_workload in target_workloads:
    if this_target_workload != "ALL" and this_target_workload != target_workload:
        continue
    dict_cat_tuningtime_order[labelmapping[target_workload]] = []
    dict_cat_tuningtime_noorder[labelmapping[target_workload]] = []
    for order_str in ["0", "1"]:
        xdb_name = xdb_dire + f"/nvme_mlc_{target_workload}_{order_str}/"
        time_file = open(xdb_name + f"Training_{target_workload}.log", "r")
        tmp = []
        lines = time_file.readlines()
        t = 0
        for l in lines:
            l = l.split(" ")
            t += float(l[1]) + float(l[2])
            tmp.append([t, float(l[4])])
        if order_str == "0":
            dict_cat_tuningtime_noorder[labelmapping[target_workload]] = tmp
        else:
            dict_cat_tuningtime_order[labelmapping[target_workload]] = tmp

import json
f = open("../reproduced_dat/tuning_time.dat", "w")
f.write(json.dumps([dict_cat_tuningtime_noorder, dict_cat_tuningtime_order]))
f.close()

