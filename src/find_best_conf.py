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

# configuration choices dictionary
# Categorical
# Discrete
# Continuous
# Boolean

# database metadata 
# configuration this in command line
import sys

print ('Number of arguments:', len(sys.argv), 'arguments.')
print ('Argument List:', str(sys.argv))

if len(sys.argv) != 4:
    print("Usage: python3 find_best_conf.py target_workload use_tuning_order xdb_directory")
    exit()

target_workload = sys.argv[1]

if target_workload not in ["TPCC", "WebSearch", "CloudStorage", "LiveMapsBackEnd", "AdspayLoad", "MapReduce", "YCSB"]:
    print(f"workload target {target_workload} not exist.")
    exit()

use_order = True

if sys.argv[2] == "False":
    use_order = False

order_str = 0
if use_order:
    order_str = 1
xdb_dire = sys.argv[3]
xdb_name = xdb_dire + f"/nvme_mlc_{target_workload}_{order_str}/"

traces_directory = "../training_traces/"
tuning_order_directory = "../reproduced_dat/tuning_order.dat"
configuration_directory = xdb_name + "configurations/"
explored_configuration_file = "confs.json"
xdbTable_name = "xdbTable.json"
parallel_lock_file_name = "lock"
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
numericals = {} # store the configuration name 
categorical = {}
booleans = {}
for key in configuration_choices:
    for key1 in configuration_choices[key]:
        for key2 in configuration_choices[key][key1]:
            if key2 != "Flash_Parameter_Set":
                if len(configuration_choices[key][key1][key2]) > 1:
                    tunable_configuration_names.append(key2)
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

# Store a json-like configuration to a xml file with filename
def save_conf(configuration, filename, random_state=321):
    doc = Document()
    configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Seed"] = random_state
    for key in configuration:
        newElem = doc.createElement(key)
        doc.appendChild(newElem)
        for key1 in configuration[key]:
            newElem1 = doc.createElement(key1)
            newElem.appendChild(newElem1)
            for key2 in configuration[key][key1]:
                if key2 != "Flash_Parameter_Set":
                    newElem15 = doc.createElement(key2)
                    newElem1.appendChild(newElem15)
                    newElem2 = doc.createTextNode(str(configuration[key][key1][key2]))
                    newElem15.appendChild(newElem2)
                else:
                    newElem2 = doc.createElement(key2)
                    newElem1.appendChild(newElem2)
                    for key3 in configuration_choices[key][key1][key2]:
                        newElem25 = doc.createElement(key3)
                        newElem2.appendChild(newElem25)
                        newElem3 = doc.createTextNode(str(configuration[key][key1][key2][key3]))
                        newElem25.appendChild(newElem3)
    f = open(filename, "w")
    f.write(doc.toprettyxml(indent="  "))
    f.close()

import copy

# Store a vector into a specified ML file
# If refer_conf and tunable_names are specified, 
# only return encoded tunables, if the rest of parameters in configurations is same as refer_conf 
def encode_configuration_and_store(conf_vector, conf_name):
    # turn conf_vector into a json-like file:
    new_configuration = copy.deepcopy(configuration_choices)
    for key in configuration_choices["Execution_Parameter_Set"]["Host_Parameter_Set"]:
        if key in tunable_configuration_names:
            new_configuration["Execution_Parameter_Set"]["Host_Parameter_Set"][key] = conf_vector[tunable_configuration_names.index(key)]
            if key in numericals:
                if type(numericals[key][0]) == type(0.1):
                    new_configuration["Execution_Parameter_Set"]["Host_Parameter_Set"][key] = float(new_configuration["Execution_Parameter_Set"]["Host_Parameter_Set"][key])
                else:
                    new_configuration["Execution_Parameter_Set"]["Host_Parameter_Set"][key] = int(new_configuration["Execution_Parameter_Set"]["Host_Parameter_Set"][key])
        else:
            new_configuration["Execution_Parameter_Set"]["Host_Parameter_Set"][key] = configuration_choices["Execution_Parameter_Set"]["Host_Parameter_Set"][key][0]
    for key in configuration_choices["Execution_Parameter_Set"]["Device_Parameter_Set"]:
        if key == "Flash_Parameter_Set":
            continue
        elif key in tunable_configuration_names:
            new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"][key] = conf_vector[tunable_configuration_names.index(key)]
            if key in numericals:
                if type(numericals[key][0]) == type(0.1):
                    new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"][key] = float(new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"][key])
                else:
                    new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"][key] = int(new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"][key])
        else:
            new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"][key] = configuration_choices["Execution_Parameter_Set"]["Device_Parameter_Set"][key][0]
    for key in configuration_choices["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"]:
        if key in tunable_configuration_names:
            new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"][key] = conf_vector[tunable_configuration_names.index(key)]
            if key in numericals:
                if type(numericals[key][0]) == type(0.1):
                    new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"][key] = float(new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"][key])
                else:
                    new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"][key] = int(new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"][key])
        else:
            new_configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"][key] = configuration_choices["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"][key][0]
    save_conf(new_configuration, conf_name)
    return


# baseline configuration metadata
baseline_conf_name = xdb_name + "configurations/0.xml"
baseline_conf = decode_configuration(baseline_conf_name)

# constraints
# sum constraints
sum_constraints = [["Data_Cache_Capacity", "CMT_Capacity"]]
# This need to be initialized. Done!
# currently, we explore the sum constrained items on the boundary 
sum_values = []

# multiply constraints
multiply_constraints = [['Flash_Channel_Count', 'Chip_No_Per_Channel','Die_No_Per_Chip', 'Plane_No_Per_Die', 'Block_No_Per_Plane' , 'Page_No_Per_Block']]
# This need to be initialized.
multiply_values = []

# multiply constraints
multiply_constraints_lesseq = [['Flash_Channel_Count', 'Chip_No_Per_Channel'], ['Die_No_Per_Chip', 'Plane_No_Per_Die'], ['Flash_Channel_Count', 'Chip_No_Per_Channel', 'Die_No_Per_Chip', 'Plane_No_Per_Die']]
# This need to be initialized.
multiply_values_lesseq = [80, 16, 1024]

# machine information
machine_identifier = "0"

# hyper-parameters
# balance latency and throughput
alpha = 0.5
# balance target and non-target workloads
beta = 0.1
# balance exploration and exploitation
var_coeff = 8.0

# some global variables for tuning
global explored_configurations
explored_configurations = []
# xdbTable: configuration recommendation table, which is a cached version of AutoDB
# confid -> workload category -> trace name -> performance (latency/throughput/power) -1 as empty
# confid -> workload category -> hyper_parameters(format: string of "HYPER" -> "{alpha},{beta}") -> "GRADES" -> current_grade
global xdbTable
xdbTable = {}

def get_index(name):
    return tunable_configuration_names.index(name)

# Initialize the constraints based on the baseline configurations
for sumitems in sum_constraints:
    baseline_sum = 0
    for itemname in sumitems:
        baseline_sum += baseline_conf[get_index(itemname)]
    sum_values.append(baseline_sum)

print(f"Sum Constraints {sum_constraints}")
print(f"Sum Constraints Values {sum_values}")

# TODO change here to multi constraints
# Initialize the constraints based on the baseline configurations
for multiplyitems in multiply_constraints:
    baseline_multi = 1
    for itemname in multiplyitems:
        baseline_multi *= baseline_conf[get_index(itemname)]
    multiply_values.append(baseline_multi)

print(f"Multiply Constraints {multiply_constraints}")
print(f"Multiply Constraints Values {multiply_values}")

def find_upper_(num):
    ini = 2
    while ini < num:
        ini *= 2
    return ini

# check whether configuration satisfy multiply and sum constraints
# power constraints are evaluated in the final phase. 
def check_conf_ok(conf_vec):
    for i in range(len(sum_values)):
        # print(f" *** check sum {i}:")
        check_sum = 0
        for itemname in sum_constraints[i]:
            # print(f" ** value {conf_vec[get_index(itemname)]}:")
            check_sum += conf_vec[get_index(itemname)]
        # print(f" * final value {check_sum} < {sum_values[i]}:")
        if check_sum != sum_values[i]:
            # print(f"failed!")
            return False
    for i in range(len(multiply_constraints)):
        # print(f" *** check multi {i}:")
        check_multi = 1
        for itemname in multiply_constraints[i]:
            # print(f" ** value {conf_vec[get_index(itemname)]}:")
            check_multi *= conf_vec[get_index(itemname)]
        # print(f" * final value {check_multi} < {multiply_values[i]}:")
        if check_multi > find_upper_(multiply_values[i]) or check_multi < 0.9 * multiply_values[i]:
            # print(f"failed 2!")
            return False
    # chip manufacturing constraints
    multi_values = []
    # input()
    for i in range(len(multiply_constraints_lesseq)):
        # print(f" *** check multi {i}:")
        check_multi = 1
        for itemname in multiply_constraints_lesseq[i]:
            # print(f" ** value {conf_vec[get_index(itemname)]}:")
            check_multi *= conf_vec[get_index(itemname)]
        # print(f" * final value {check_multi} < {multiply_values_lesseq[i]}:")
        if i == 0 and (check_multi > multiply_values_lesseq[i] or check_multi < int(multiply_values_lesseq[i] / 2)):
            # print("Conf Failed!")
            return False
        if i != 0 and (check_multi > multiply_values_lesseq[i] or check_multi < int(multiply_values_lesseq[i] / 4)):
            # print("Conf Failed!")
            return False
        multi_values.append(check_multi)
    if multi_values[0] > 64 and multi_values[1] > 8:
        # print("Conf Failed!")
        return False
    # print("Conf OK!")
    return True

# candidates cannot violate two constraints at the same time!
def adjust_configurations_based_on_constraints(candidates, name):
    tuned_candidates = []
    clean = True
    # print(f"Adjust based on constraints {name}")
    for sumitems in sum_constraints:
        if name in sumitems:
            clean = False
            for itemname in sumitems:
                if itemname != name:
                    for can in candidates:
                        new_conf = can.copy()
                        adj_idx = get_index(itemname)
                        for value in numericals[itemname]:
                            new_conf[adj_idx] = value
                            if check_conf_ok(new_conf):
                                tuned_candidates.append(new_conf.copy())
    for multiplyitems in multiply_constraints:
        if name in multiplyitems:
            clean = False
            for itemname1 in multiplyitems:
                if itemname1 != name:
                    for itemname2 in multiplyitems:
                        if itemname2 != name and itemname2 != itemname1:
                            # print(f"Adjust  {itemname1}  {itemname2} By {name}")
                            for can in candidates:
                                new_conf = can.copy()
                                adj_idx1 = get_index(itemname1)
                                adj_idx2 = get_index(itemname2)
                                # print(f"ORIGIN {can[adj_idx1]} {can[adj_idx2]} and {can[get_index(name)]}")
                                for value1 in numericals[itemname1]:
                                    # manhattan distance, we change it into direct value constraints
                                    if value1 < can[adj_idx1] / 2 or value1 > can[adj_idx1] * 2:
                                        continue
                                    for value2 in numericals[itemname2]:
                                        new_conf[adj_idx1] = value1
                                        new_conf[adj_idx2] = value2
                                        # print(f"Tune {new_conf[adj_idx1]} {new_conf[adj_idx2]}")
                                        # print(f"From {numericals[itemname1]} {numericals[itemname2]}")
                                        if check_conf_ok(new_conf):
                                            tuned_candidates.append(new_conf.copy())
    if clean:
        tuned_candidates = candidates
    # print(f"{name} After adjustment: {len(tuned_candidates)} candidate configurations")
    # input()
    return tuned_candidates

# SGD: Subroutine, find adjacent configurations using the configuration vector
def adjacent_configurations(conf_vec, tunable_names):
    # For all the tunables, tune them based on the constraints.
    # Find the adjacent value in configuration_choices and return all the acjacent configuration that still satisfy the constraints
    adj_confs = []
    # Iterate through all the tunable parameters. give one step foward. 
    for name in tunable_names:
        idx = get_index(name)
        candidates = []
        # TUNABLES HERE generate adjacent configuration for idx
        if name in numericals: # for numerical configurations, we choose the number that is >= 0.5x current and <= 2x current as neighbour. 
            cur_value = conf_vec[idx] 
            new_conf_count = 0
            for value in numericals[name]:
                if (value >= 0.5 * cur_value or value <= 2 * cur_value) and value != cur_value:
                    new_conf = conf_vec.copy()
                    new_conf[idx] = value
                    candidates.append(new_conf)
                    new_conf_count += 1
            if new_conf_count < 2:
                for value in numericals[name]:
                    if (value >= 0.5 * cur_value or value <= 2 * cur_value) and value != cur_value:
                        new_conf = conf_vec.copy()
                        new_conf[idx] = value
                        if new_conf not in candidates:
                            candidates.append(new_conf)
                            new_conf_count += 1
            # now, according to the constraints adjust the value of the adjacent configurations
            candidates = adjust_configurations_based_on_constraints(candidates, name)
        elif name in booleans:
            for value in booleans[name]:
                if value != conf_vec[idx]:
                    new_conf = conf_vec.copy()
                    new_conf[idx] = value
                    candidates.append(new_conf)
        elif name in categorical:
            for value in categorical[name]:
                if value != conf_vec[idx]:
                    new_conf = conf_vec.copy()
                    new_conf[idx] = value
                    candidates.append(new_conf)
        for it in candidates:
            if it not in adj_confs:
                adj_confs.append(it)
    print(f"Found {len(adj_confs)} adjacent configurations.")
    return adj_confs

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import DotProduct, WhiteKernel, RBF, RationalQuadratic
import time
import json
import math
import random
random.seed(20231029)

conf_file = xdb_name + explored_configuration_file
xdbTable_file = xdb_name + xdbTable_name
lock_file = xdb_name + parallel_lock_file_name

# simple lock for parallel operations on autoDB
def auto_lock():
    while(1):
        try:
            f = open(lock_file, "r+")
        except:
            f = open(lock_file, "w+")
            f.close()
            continue
        if len(f.read()) > 0:
            f.close()
            time.sleep(1)
        else:
            # TODO use os.replace to make it atomic. Not necessary now since there are poor parallelism on writing this file
            f.write(str(machine_identifier))
            f.close()
            break
    return True

def auto_unlock():
    try:
        f = open(lock_file, "r+")
    except:
        f = open(lock_file, "w+")
        f.close()
        return
    f.truncate()
    f.close()
    return True

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
# auto_lock()
# calculate_grade()
# auto_unlock()
# 
def update_xdb(xdbTable, explored_configurations, configuration_updates, xdbTable_updates, workload_cat, table=False, confs=False):
    print("Update XDB!")
    auto_lock()
    f = open(xdbTable_file, "r")
    xdbTable = json.loads(f.read())
    f.close()
    f = open(conf_file, "r")
    explored_configurations = json.loads(f.read())
    f.close()
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
    auto_unlock()
    print("Update Finished!")
    return xdbTable, explored_configurations

def get_grade(xdbTable, confid, workload_cat):
    grade = [-1,-1,[-1, -1]]
    if "INVALID" == xdbTable[confid]:
        print("DEBUG: SHOULD NOT REACH HERE. ID=2")
        return -1
    elif "HYPER" not in xdbTable[confid][workload_cat]:
        grade = calculate_grade(xdbTable, confid, workload_cat)
        print("DEBUG: SHOULD NOT REACH HERE. ID=1")
    else:
        if alpha == float(xdbTable[confid][workload_cat]["HYPER"][0]) and beta == float(xdbTable[confid][workload_cat]["HYPER"][1]):
            grade = xdbTable[confid][workload_cat]["HYPER"][2]
        else:
            grade = calculate_grade(xdbTable, confid, workload_cat)
            print("WARNING: You are changing the hyper parameters, reload the xdbTable to avoid constant re-calculation.")
    return grade

# search the database for next search roots
def get_search_root(workload_cat, xdbTable, max_root=3):
    root_confid = [0, 0, 0]
    best_grade = [0, 0, 0]
    for confid in xdbTable:
        if "INVALID" in xdbTable[confid]:
            continue
        if workload_cat not in xdbTable[confid]:
            continue
        grade = get_grade(xdbTable, confid, workload_cat)
        if float(grade[2][0]) < 0.9 or float(grade[2][1]) < 0.9:
            continue
        grade = float(grade[0])
        if grade > best_grade[0]:
            best_grade[2] = best_grade[1]
            best_grade[1] = best_grade[0]
            best_grade[0] = grade
            root_confid[2] = root_confid[1]
            root_confid[1] = root_confid[0]
            root_confid[0] = int(confid)
        elif grade > best_grade[1]:
            best_grade[2] = best_grade[1]
            best_grade[1] = grade
            root_confid[2] = root_confid[1]
            root_confid[1] = int(confid)
        elif grade > best_grade[2]:
            best_grade[2] = grade
            root_confid[2] = int(confid)
    return root_confid[random.randint(0,max_root - 1)]

def encode_configuration(conf_vec):
    encoded_vec = []
    for name in tunable_configuration_names:
        value = conf_vec[get_index(name)]
        if name in numericals:
            encoded_vec.append(numericals[name].index(value))
        elif name in booleans:
            encoded_vec.append(booleans[name].index(value))
        elif name in categorical:
            total = len(categorical[name])
            idx = categorical[name].index(value)
            for i in range(idx):
                encoded_vec.append(0)
            encoded_vec.append(1)
            for i in range(total - idx - 1):
                encoded_vec.append(0)
    return encoded_vec

# GPR: initialize GPR model with given configuration_performance pair
# the configuration is encoded with the index in the booleans/categorical/numericals values
# and return the model
# input : configuration id in explored_configurations
# output: trained gpr model
def initialized_gpr(configuration_ids, workload_cat, xdbTable, explored_configurations):
    # first, encode all existing configurations and their performance
    encoded_confs = []
    encoded_perfs  =[]
    for idx in configuration_ids:
        if str(idx) not in xdbTable:
            continue
        if "INVALID" == xdbTable[str(idx)]:
            continue
        encoded_perfs.append(float(get_grade(xdbTable, str(idx), workload_cat)[0]))
        encoded_confs.append(encode_configuration(explored_configurations[int(idx)]))
    X = encoded_confs
    y = encoded_perfs
    # print(encoded_perfs)
    kernel = 1e3 * RBF(length_scale=10, length_scale_bounds=(1e-20,1e10)) + 1e3 * RationalQuadratic(alpha=1, length_scale=1,alpha_bounds=(1e-20,1e10), length_scale_bounds=(1e-20,1e10)) +WhiteKernel(noise_level=1e3, noise_level_bounds=(1e-20,1e10))
    gpr = GaussianProcessRegressor(kernel=kernel, random_state=65536).fit(np.array(X), np.array(y))
    return gpr


# SGD: find optimized configuration in the given group, with a trained gpr model
# TODO Manhattan distance
def find_optimized_in_group(conf_vecs, gpr, with_order=False, order_list=None):
    encoded_test_confs = []
    for c in conf_vecs:
        encoded_test_confs.append(encode_configuration(c))
    max_id = 0
    prediction = gpr.predict([encoded_test_confs[0]], return_std=True)
    cur_max_grade = prediction[0] + var_coeff * prediction[1]
    all_grades = [[prediction[0], prediction[1], cur_max_grade]]
    equal_candidates = []
    for i in range(1, len(encoded_test_confs)):
        prediction = gpr.predict([encoded_test_confs[i]], return_std=True)
        grade = prediction[0] + var_coeff * prediction[1]
        all_grades.append([prediction[0], prediction[1], grade])
        if grade > cur_max_grade * 1.05:
            cur_max_grade = grade
            max_id = i
            new_equal_candidates = [[grade, i]]
            for item in equal_candidates:
                if item[0] >= cur_max_grade * 0.95 and item[0] <= cur_max_grade * 1.05:
                    new_equal_candidates.append(item)
            equal_candidates = new_equal_candidates
        elif grade >= cur_max_grade * 0.95 and grade <= cur_max_grade * 1.05:
            equal_candidates.append([grade, i])
    if len(equal_candidates) > 1:
        # no order
        # print("In equal dicision!")
        if not with_order:
            select = equal_candidates[random.randint(0, len(equal_candidates) - 1)]
            cur_max_grade = select[0]
            max_id = select[1]
        elif target_workload == "CloudStorage" or target_workload == "AdspayLoad":
            candidates_and_order = []
            for grade, i in equal_candidates:
                val = 1
                for j in order_list[0]:
                    val *= conf_vecs[i][j]
                val1 = 1
                for j in order_list[1]:
                    val1 *= conf_vecs[i][j]
                candidates_and_order.append([i, val, grade, val1, conf_vecs[i][order_list[1][1]]])
            sorted_candidates = sorted(candidates_and_order, key=lambda x:(- x[1] - 256 * x[4] - 256 * x[3]))
            print(len(sorted_candidates))
            # tuning order - layout is most important
            sorted_candidates = sorted_candidates[0:int(len(sorted_candidates) / 2) + 1]
            # we should still preserve the tuning of other parameters
            select = sorted_candidates[random.randint(0, len(sorted_candidates) - 1)]
            print(sorted_candidates.index(select))
            cur_max_grade = select[2]
            max_id = select[0]
        else:
            candidates_and_order = []
            for grade, i in equal_candidates:
                val = 1
                for j in order_list[0]:
                    val *= conf_vecs[i][j]
                val1 = 1
                for j in order_list[1]:
                    val1 *= conf_vecs[i][j]
                candidates_and_order.append([i, val, grade, val1])
            sorted_candidates = sorted(candidates_and_order, key=lambda x:(- 256 * x[1] - x[3]))
            print(len(sorted_candidates))
            # tuning order - layout is most important
            sorted_candidates = sorted_candidates[0:int(len(sorted_candidates) / 2) + 1]
            # we should still preserve the tuning of other parameters
            select = sorted_candidates[random.randint(0, len(sorted_candidates) - 1)]
            print(sorted_candidates.index(select))
            cur_max_grade = select[2]
            max_id = select[0]
    # print(f"DEBUG: Selected Best Configuration {max_id} of grade {all_grades[max_id]} among {all_grades[0:int(len(all_grades) / 10)]} ...")
    return conf_vecs[max_id]


def print_best_conf(workload_cat, explored_configurations):
    grades = []
    maxid = 0
    maxval = 0
    target_improvement = 0
    # check whether hurt the non-target workload
    for i in range(len(explored_configurations)):
        if str(i) not in xdbTable:
            continue
        if "INVALID" == xdbTable[str(i)]:
            continue
        grade = get_grade(xdbTable, str(i), workload_cat)
        if float(grade[2][0] < 1.0 or grade[2][1]) < 1.0:
            continue
        tmp_target = float(grade[1])
        grade = float(grade[0])
        grades.append(grade)
        if grades[-1] > maxval:
            maxval = grades[-1]
            maxid = i
            target_improvement = tmp_target
    print(f"Current Best configuration {maxid}, with max grade {maxval}")
    return maxval, maxid, target_improvement


# workload_cat -> trace names
all_traces = {}
skip_list = ["FINANCIAL", "VDI", "DevTool", "FIUHome", "MSN", "PageRank", "CloudStorageTest", "MLPrep", "YCSBTest", "RadiusAuth", "TPCCTest"]
def load_trace_names():
    traces = os.listdir(traces_directory)
    for tname in traces:
        if tname.endswith("0-0-0"):
            continue
        workload_cat = tname.split("-")[0]
        if workload_cat in skip_list:
            continue
        if workload_cat not in all_traces:
            all_traces[workload_cat] = []
        if tname not in all_traces[workload_cat]:
            all_traces[workload_cat].append(tname)
    for cat in all_traces:
        all_traces[cat] = sorted(all_traces[cat], key=lambda x: (int(x.split("-")[1]) * 10000 + int(x.split("-")[2]) * 100 + int(x.split("-")[3])))
    
def trace_performed(configid, workload_cat, tracename, check_power=False):
    if str(configid) not in xdbTable:
        return False
    if workload_cat not in xdbTable[str(configid)]:
        return False
    if tracename not in xdbTable[str(configid)][workload_cat]:
        return False
    if check_power and -1 == xdbTable[str(configid)][workload_cat][tracename][2]:
        return False
    return True


# return the validation results in the format of dictionary
# 
# if does not satisfy power constraint, simulator will return with {"ERROR" : "Power"}
# else if this branch is pruned (see the paper), simulator will return with {"PRUNED" : "Bad Conf"}
# else return {cate: [lat_improv, thpt_improv]}
# for what-if analysis, we do not check the power constraints.
def simulator_validation(confid, workload_cat, xdbTable, explored_configurations, check_power=False):
    print(f"Simulator Evaluation for Trace {workload_cat} on configuration {confid}")
    time_start = time.time()
    # store configuration to conf directory
    encode_configuration_and_store(explored_configurations[int(confid)], configuration_directory + str(confid) + ".xml")
    # load traces
    if workload_cat not in all_traces:
        load_trace_names()
        if workload_cat not in all_traces:
            print(f"ERROR: Validation does not have certain workload type {workload_cat}")
    i = 0
    current_perform_tracename = all_traces[workload_cat][0] # get target workload name
    while trace_performed(confid, workload_cat, current_perform_tracename):
        i = i + 1
        if i >= len(all_traces[workload_cat]):
            i = 0
            break
        current_perform_tracename = all_traces[workload_cat][i]
    current_non_target_tracenames = [] # get non-target workload name
    for cat in all_traces:
        if cat == workload_cat:
            continue
        i = 0
        tmp = all_traces[cat][0] # get target workload name
        while trace_performed(confid, cat, tmp):
            i = i + 1
            if i >= len(all_traces[cat]):
                i = 0
                break
            tmp = all_traces[cat][i]
        current_non_target_tracenames.append(tmp)
    confs = [str(confid) + ".xml", str(0) + ".xml"]
    if int(confid) == 0:
        confs = [str(confid) + ".xml"]
    tracenames = current_non_target_tracenames + [current_perform_tracename]
    print(f"Batch Execution: {confs} {tracenames} ")
    batch_exec(configuration_directory[0:-1], traces_directory, confs, tracenames)
    print(f"Batch Execution Done! Start Update xdbTable")
    xdbTable_updates = {str(confid) : {}, str(0) : {}}
    time_end = time.time()
    print(f"Evaluation done, time spent {time_end - time_start}")
    for t in tracenames:
        cat = t.split("-")[0]
        result = evaluate_config_workload(configuration_directory + str(confid) + ".xml", traces_directory + t)
        if not result: # This configuration is not valid, which cause the simulator to crase
            xdbTable_updates[str(confid)] = "INVALID"
            break
        xdbTable_updates[str(confid)][cat] = {}
        xdbTable_updates[str(confid)][cat][t] = [result[0], result[4], -1]
        if int(confid) != 0:
            result = evaluate_config_workload(configuration_directory + str(0) + ".xml", traces_directory + t)
            xdbTable_updates[str(0)][cat] = {}
            xdbTable_updates[str(0)][cat][t] = [result[0], result[4], -1]
    configuration_updates = []
    # print(f"DEBUG; updates {xdbTable_updates}")
    return update_xdb( xdbTable, explored_configurations, configuration_updates, xdbTable_updates, workload_cat, table=True)

if __name__ == "__main__":
    # load initial value
    xdbTable, explored_configurations = update_xdb(xdbTable, explored_configurations, [baseline_conf], {}, target_workload, True, True)
    
    print(f"Initial config:{explored_configurations} xdbTable: {xdbTable}")
    
    if "0" not in xdbTable:
        print(f"First validate baseline configuration.")
        xdbTable, explored_configurations = simulator_validation(0, target_workload, xdbTable, explored_configurations)
    
    print(f"Training Start! Target workload: {target_workload}")
    
    # load training order
    
    # tuning_order = [["Flash_Channel_Count", "Chip_No_Per_Channel", "Die_No_Per_Chip", "Plane_No_Per_Die", "Block_No_Per_Plane", "Page_No_Per_Block"], ["Data_Cache_Capacity", "CMT_Capacity"], ["Plane_Allocation_Scheme"]]
    # if target_workload == "WebSearch":
    #     tuning_order = [["Data_Cache_Capacity", "CMT_Capacity"], ["Plane_Allocation_Scheme"],["Flash_Channel_Count", "Chip_No_Per_Channel", "Die_No_Per_Chip", "Plane_No_Per_Die", "Block_No_Per_Plane", "Page_No_Per_Block"]]
    # if target_workload == "LivemapsbackEnd":
    #     tuning_order = [["Plane_Allocation_Scheme"], ["Data_Cache_Capacity", "CMT_Capacity"], ["Flash_Channel_Count", "Chip_No_Per_Channel", "Die_No_Per_Chip", "Plane_No_Per_Die", "Block_No_Per_Plane", "Page_No_Per_Block"]]
    f = open(tuning_order_directory, "r")
    all_orders = json.loads(f.read())
    f.close()
    if target_workload not in all_orders:
        print("Tuning order not generated! please generate order with pruning data first!")
        exit()
    tuning_order = all_orders[target_workload]
    if not use_order:
        skipped_parameters_for_this_exp = ["IO_Queue_Depth", "Queue_Fetch_Size", "Block_Erase_Latency", "Page_Program_Latency_MSB", "Page_Program_Latency_CSB","Page_Program_Latency_LSB", "Page_Read_Latency_MSB", "Page_Read_Latency_CSB", "Page_Read_Latency_LSB"]
        all_tuning_variables = []
        for name in tunable_configuration_names:
            if name not in skipped_parameters_for_this_exp:
                all_tuning_variables.append(name)
        tuning_order = [all_tuning_variables]
    # predetermined values
    epoch = 0
    max_grade = 0.0
    max_id = 0
    no_use_threshold = 0.001
    conv_count = 0
    equal_grades = []
    current_tuning_set = 0
    time_file = open(xdb_name + f"Training_{target_workload}.log", "w")
    new_tuning_order_count = 0

    while(1):
        t_start = time.time()
        new_tuning_order_count += 1
        print(f"Epoch {epoch}:")
        new_search_root_confid = get_search_root(target_workload, xdbTable, min(new_tuning_order_count, 3))
        print(f"new search root {new_search_root_confid}")
        gpr = initialized_gpr(list(range(len(explored_configurations))), target_workload, xdbTable, explored_configurations)
        print(f"GPR initialized!")
        adj_confs = adjacent_configurations(explored_configurations[int(new_search_root_confid)], tuning_order[current_tuning_set])
        maximum_no_use_exploreation_time = 4 * len(tuning_order[current_tuning_set])
        if maximum_no_use_exploreation_time < 15:
            maximum_no_use_exploreation_time = 15
        del_confs = []
        for c in adj_confs:
            if c in explored_configurations:
                if str(explored_configurations.index(c)) in xdbTable:
                    if "INVALID" == xdbTable[str(explored_configurations.index(c))]:
                        del_confs.append(c)
        for c in del_confs:
            adj_confs.remove(c)
        del_confs = []
        for c in adj_confs:
            if c in explored_configurations:
                del_confs.append(c)
        if len(del_confs) < 0.1 * len(adj_confs):
            for c in del_confs:
                adj_confs.remove(c)
        print(f"Identified {len(adj_confs)} adjacent configurations")
        if explored_configurations[int(new_search_root_confid)] not in adj_confs:
            adj_confs.append(explored_configurations[int(new_search_root_confid)])
        # new_optimized = find_optimized_in_group(adj_confs, gpr)
        # here, we hard-code the tuning order of layout, since except for websearch, all the other workloads are most sensitive to layout 
        if use_order and "Flash_Channel_Count" in tuning_order[current_tuning_set] and target_workload != "WebSearch":
            new_optimized = find_optimized_in_group(adj_confs, gpr, use_order, [[get_index("Flash_Channel_Count"), get_index("Chip_No_Per_Channel")], [get_index('Die_No_Per_Chip'), get_index('Plane_No_Per_Die')]])
        else:
            new_optimized = find_optimized_in_group(adj_confs, gpr)
        print(f"Next candidate configuration found!")
        if new_optimized not in explored_configurations:
            xdbTable, explored_configurations = update_xdb(xdbTable, explored_configurations, [new_optimized], {}, target_workload, confs=True)
        print(f"Update Candidate Configuration To Table!")
        t_mid = time.time()
        xdbTable, explored_configurations = simulator_validation(explored_configurations.index(new_optimized), target_workload, xdbTable, explored_configurations)
        print(f"Validated Next Candidate Configuration!")
        grade, best_id, best_target_improvement = print_best_conf(target_workload, explored_configurations)
        if grade > max_grade * 1.01  and max_grade >= 0.1:
            max_grade = grade
            max_id = best_id
            new_eq = []
            for g, cid in equal_grades:
                if g > max_grade * 0.99 and g <= max_grade * 1.01:
                    new_eq.append([g, cid])
            equal_grades = new_eq
            conv_count = 0
        else:
            conv_count += 1
        if grade > max_grade * 0.99 and grade <= max_grade * 1.01:
            equal_grades.append([grade, best_id])
        print(f"Current Max Grade {max_id}, Conv Counter {conv_count}, euqal_cand {len(equal_grades)}, grade range {max_grade * 0.99} - {max_grade * 1.01}")
        print(f"Current Best Configuration Printed.")
        if conv_count > maximum_no_use_exploreation_time or len(equal_grades) > 20:
            print(f"Convergence Reached.")
            conv_count = 0
            current_tuning_set += 1
            if current_tuning_set >= len(tuning_order):
                break
            else:
                new_tuning_order_count = 0
        t_end = time.time()
        print(f"Duration of Epoch {epoch} is {t_end - t_start}.")
        epoch += 1
        time_file.write(f"{epoch} {t_mid - t_start} {t_end - t_mid} {explored_configurations.index(new_optimized)} {best_target_improvement}\n")
        # input()
        if epoch > 100:
            print("outreach convergence limit, converging...")
            exit()


