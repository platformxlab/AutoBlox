# this file is used to generate confiugurations for 

import os
import time
import numpy as np
import json
# configuration to XML file
from xml.dom.minidom import Document
import xml
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

def save_workload(configuration, trace_dir, filename, input_filename, output_filename):
    channel_num = configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Channel_Count"]
    chip_num = configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Chip_No_Per_Channel"]
    die_num = configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"]["Die_No_Per_Chip"]
    plane_num = configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"]["Plane_No_Per_Die"]
    workload_str = """<?xml version="1.0" encoding="us-ascii"?>
    <MQSim_IO_Scenarios>
            <IO_Scenario>
                    <IO_Flow_Parameter_Set_Trace_Based>
                            <Priority_Class>HIGH</Priority_Class>
                            <Device_Level_Data_Caching_Mode>WRITE_READ_CACHE</Device_Level_Data_Caching_Mode>
                            <Channel_IDs>{}</Channel_IDs>
                            <Chip_IDs>{}</Chip_IDs>
                            <Die_IDs>{}</Die_IDs>
                            <Plane_IDs>{}</Plane_IDs>
                            <Initial_Occupancy_Percentage>20</Initial_Occupancy_Percentage>
                            <Cache_Input_Filename>{}</Cache_Input_Filename>
                            <Cache_Output_Filename>{}</Cache_Output_Filename>
                            <File_Path>{}</File_Path>
                            <Percentage_To_Be_Executed>100</Percentage_To_Be_Executed>
                            <Relay_Count>1</Relay_Count>
                            <Time_Unit>NANOSECOND</Time_Unit>
                    </IO_Flow_Parameter_Set_Trace_Based>
            </IO_Scenario>
    </MQSim_IO_Scenarios>""".format(str(list(range(0, channel_num)))[1:-1], 
                                    str(list(range(0, chip_num)))[1:-1], 
                                    str(list(range(0, die_num)))[1:-1],
                                    str(list(range(0, plane_num)))[1:-1], 
                                    input_filename, 
                                    output_filename,
                                    trace_dir)
    f = open(filename, "w")
    f.write(workload_str)
    f.close()

def store_trace(dir, io_vec):
    f = open(dir, "w")
    for io in io_vec:
        for i in range(0, len(io)):
            io[i] = str(io[i])
        f.write(" ".join(io) + "\n")
    f.close()

def get_performance(fname):
    DOMTree = xml.dom.minidom.parse(fname)
    collection = DOMTree.documentElement
    results = collection.getElementsByTagName("Host")[0]
    results = results.getElementsByTagName("Host.IO_Flow")[0]
    elatency = results.getElementsByTagName("Device_Response_Time")[0]
    emaxlatency = results.getElementsByTagName("Max_Device_Response_Time")[0]
    eteRes = results.getElementsByTagName("End_to_End_Request_Delay")[0]
    maxeteRes = results.getElementsByTagName("Max_End_to_End_Request_Delay")[0]
    ioPS = results.getElementsByTagName("Bandwidth")[0]
    ReqGen = results.getElementsByTagName("Request_Count")[0]
    ReqServ = results.getElementsByTagName("Serviced_Request_Count")[0]
    return [float(elatency.childNodes[0].data), float(emaxlatency.childNodes[0].data),
            float(eteRes.childNodes[0].data), float(maxeteRes.childNodes[0].data),float(ioPS.childNodes[0].data), int(ReqGen.childNodes[0].data), int(ReqServ.childNodes[0].data)]

# configuration to dict
def conf2dict_pruning(conf, thisid):
    # test configuration set
    counter = 0
    configuration = {}
    for key in configuration_choices:
        configuration[key] = dict()
        for key1 in configuration_choices[key]:
            configuration[key][key1] = dict()
            for key2 in configuration_choices[key][key1]:
                if key2 != "Flash_Parameter_Set":
                    # print("current:[{}][{}][{}][{}], counter = {}".format(key, key1, key2, conf[counter], counter))
                    if counter == thisid:
                        configuration[key][key1][key2] = configuration_choices[key][key1][key2][conf[counter]]
                    else:
                        configuration[key][key1][key2] = configuration_base[key][key1][key2][0]
                    counter += 1
                else:
                    configuration[key][key1][key2] = dict()
                    for key3 in configuration_choices[key][key1][key2]:
                        if counter == thisid:
                            configuration[key][key1][key2][key3] = configuration_choices[key][key1][key2][key3][conf[counter]]
                        else:
                            configuration[key][key1][key2][key3] = configuration_base[key][key1][key2][key3][0]
                        counter += 1
    return configuration

import subprocess

configuration_base = {
    "Execution_Parameter_Set" : {
        "Host_Parameter_Set" : {
            "PCIe_Lane_Bandwidth" : [1.0], # ! 1Gb/s for PCIe 3, 1 times greater every next gen, PCIe 6 released in 2021 
            "PCIe_Lane_Count" : [4], # ! 1, 2, 4, 8, 16x Type
            "SATA_Processing_Delay" : [400000], # ！ consist with ben
            "Enable_ResponseTime_Logging" : ["false"], # * simulation para
            "ResponseTime_Logging_Period_Length" : [1000000], # * simulation para
        },
        "Device_Parameter_Set" : {
            "Seed" : [321], # *  should be randomly set,currently just stay the same to replay results
            "Enabled_Preconditioning" : ["true"], # *  preconditioning set to true to se better performance
            "Memory_Type" : ["FLASH"], # ? No other for our simulator
            "HostInterface_Type" : ["NVME"], # ! Two Kind of Interfaces Here
            "IO_Queue_Depth" : [4], # ! ? By increasing, Latency up but throughput up too,
            "Queue_Fetch_Size" : [4], # ? should do more survey on SSDs 
            "Caching_Mechanism" : ["ADVANCED"], # ?!!! will add new cache strategy here 
            "Data_Cache_Sharing_Mode" : ["SHARED"], # 
            "Data_Cache_Capacity" : [838860800],
            "Data_Cache_DRAM_Row_Size" : [4096],
            "Data_Cache_DRAM_Data_Rate" : [400], # for bus frequency of 100 MHz, DDR SDRAM 200GT/s
            "Data_Cache_DRAM_Data_Busrt_Size" : [2], # Chip Num
            "Data_Cache_DRAM_tRCD" : [14],
            "Data_Cache_DRAM_tCL" : [14],
            "Data_Cache_DRAM_tRP" : [14],
            "Address_Mapping" : ["PAGE_LEVEL"], # no hibrid, buggy
            "Ideal_Mapping_Table" : ["false"], # * should be false to be realistic
            "CMT_Capacity" : [2097152],
            "CMT_Sharing_Mode" : ["SHARED"],
            "Plane_Allocation_Scheme" : ["CWDP"],
            "Transaction_Scheduling_Policy" : ["PRIORITY_OUT_OF_ORDER"],
            "Overprovisioning_Ratio" : [0.2],
            "GC_Exec_Threshold" : [0.1],
            "GC_Block_Selection_Policy" : ["GREEDY"],
            "Use_Copyback_for_GC" : ["false"],
            "Preemptible_GC_Enabled" : ["true"],
            "GC_Hard_Threshold" : [0.05],
            "Dynamic_Wearleveling_Enabled" : ["true"],
            "Static_Wearleveling_Enabled" : ["true"],
            "Static_Wearleveling_Threshold" : [100], # ?????????
            "Preferred_suspend_erase_time_for_read" : [100000],
            "Preferred_suspend_erase_time_for_write" : [100000],
            "Preferred_suspend_write_time_for_read" : [100000],
            "Flash_Channel_Count" : [12], # most regular channel count
            "Flash_Channel_Width" : [8], # my understanding, how much bandwith for each channel. more search needed.
            "Channel_Transfer_Rate" : [400],
            "Chip_No_Per_Channel" : [5],
            "Flash_Comm_Protocol" : ["NVDDR2"],
            "Flash_Parameter_Set" : {
                "Flash_Technology" : ["MLC"], # Seems this should be fixed
                "CMD_Suspension_Support" : ["NONE"],
                "Page_Read_Latency_LSB" : [6250],
                "Page_Read_Latency_CSB" : [50000],
                "Page_Read_Latency_MSB" : [50000],
                "Page_Program_Latency_LSB" : [500000],
                "Page_Program_Latency_CSB" : [6250],
                "Page_Program_Latency_MSB" : [500000],
                "Block_Erase_Latency" : [3800000],
                "Block_PR_Cycles_Limit" : [10000],
                "Suspend_Erase_Time" : [700000],
                "Suspend_Program_time" : [100000],
                "Die_No_Per_Chip" : [8],
                "Plane_No_Per_Die" : [1],
                "Block_No_Per_Plane" : [512],
                "Page_No_Per_Block" : [512],
                "Page_Capacity" : [4096],
                "Page_Metadat_Capacity" : [448],
            },
        }
    }
}

configuration_choices = {
    "Execution_Parameter_Set" : {
        "Host_Parameter_Set" : {
            "PCIe_Lane_Bandwidth" : [0.5, 1.0, 2.0, 4.0, 8.0], # ! 1Gb/s for PCIe 3, 1 times greater every next gen, PCIe 6 released in 2021 
            "PCIe_Lane_Count" : [2, 4, 8, 16, 32], # ! 1, 2, 4, 8, 16x Type
            "SATA_Processing_Delay" : [100000, 200000, 400000, 800000, 1600000], # ！ consist with ben
            "Enable_ResponseTime_Logging" : ["false"], # * simulation para
            "ResponseTime_Logging_Period_Length" : [1000000,2000000,4000000,8000000,16000000], # * simulation para
        },
        "Device_Parameter_Set" : {
            "Seed" : [321], # *  should be randomly set,currently just stay the same to replay results
            "Enabled_Preconditioning" : ["true"], # *  preconditioning set to true to se better performance
            "Memory_Type" : ["FLASH"], # ? No other for our simulator
            "HostInterface_Type" : ["NVME"], # ! Two Kind of Interfaces Here
            "IO_Queue_Depth" : [4, 8, 16, 32, 64], # ! ? By increasing, Latency up but throughput up too,
            "Queue_Fetch_Size" : [2, 4, 8, 16, 32], # ? should do more survey on SSDs 
            "Caching_Mechanism" : ["ADVANCED"], # ?!!! will add new cache strategy here 
            "Data_Cache_Sharing_Mode" : ["SHARED"], # 
            "Data_Cache_Capacity" : [209715200, 419430400, 838860800, 1677721600, 3355443200],
            "Data_Cache_DRAM_Row_Size" : [1024, 2048, 4096, 8192, 16384],
            "Data_Cache_DRAM_Data_Rate" : [100, 200, 400, 800, 1600, 2133], # for bus frequency of 100 MHz, DDR SDRAM 200GT/s
            "Data_Cache_DRAM_Data_Busrt_Size" : [1, 2, 4, 8, 16], # Chip Num
            "Data_Cache_DRAM_tRCD" : [14],
            "Data_Cache_DRAM_tCL" : [14],
            "Data_Cache_DRAM_tRP" : [14],
            "Address_Mapping" : ["PAGE_LEVEL"], # no hibrid, buggy
            "Ideal_Mapping_Table" : ["false"], # * should be false to be realistic
            "CMT_Capacity" :[1048576, 2097152, 4194304, 8388608, 134217728],
            "CMT_Sharing_Mode" : ["SHARED"],
            "Plane_Allocation_Scheme" : ["CWDP", "CWPD", "CDWP", "CDPW", "CPWD", "CPDW", "WCDP", "WCPD", "WDCP", "WDPC", "WPCD", "WPDC", "DCWP", "DCPW", "DWCP", "DWPC", "DPCW", "DPWC", "PCWD", "PCDW", "PWCD", "PWDC", "PDCW", "PDWC"],
            "Transaction_Scheduling_Policy" : ["PRIORITY_OUT_OF_ORDER"],
            "Overprovisioning_Ratio" : [  0.025, 0.05, 0.1, 0.2, 0.4],
            "GC_Exec_Threshold" : [0.025, 0.05, 0.1, 0.2, 0.4],
            "GC_Block_Selection_Policy" : ["GREEDY", "RGA", "RANDOM", "RANDOM_P", "RANDOM_PP", "FIFO"],
            "Use_Copyback_for_GC" : ["true", "false"],
            "Preemptible_GC_Enabled" : ["true", "false"],
            "GC_Hard_Threshold" : [0.05],
            "Dynamic_Wearleveling_Enabled" : ["true", "false"],
            "Static_Wearleveling_Enabled" : ["true", "false"],
            "Static_Wearleveling_Threshold" : [100, 200, 400, 800, 1600], # ?????????
            "Preferred_suspend_erase_time_for_read" : [25000, 50000, 100000, 200000, 400000],
            "Preferred_suspend_erase_time_for_write" : [25000, 50000, 100000, 200000, 400000],
            "Preferred_suspend_write_time_for_read" : [25000, 50000, 100000, 200000, 400000],
            "Flash_Channel_Count" : [12], # most regular channel count
            "Flash_Channel_Width" : [2, 4, 8, 16, 32], # my understanding, how much bandwith for each channel. more search needed.
            "Channel_Transfer_Rate" : [100, 200, 400, 800, 1600],
            "Chip_No_Per_Channel" : [5],
            "Flash_Comm_Protocol" : ["NVDDR2"],
            "Flash_Parameter_Set" : {
                "Flash_Technology" : ["MLC"], # Seems this should be fixed
                "CMD_Suspension_Support" : ["NONE", "PROGRAM", "PROGRAM_ERASE", "ERASE"],
                "Page_Read_Latency_LSB" : [6250, 12500, 25000, 50000,  100000],
                "Page_Read_Latency_CSB" : [6250, 12500, 25000, 50000,  100000],
                "Page_Read_Latency_MSB" : [6250, 12500, 25000, 50000, 100000],
                "Page_Program_Latency_LSB" : [6250, 125000,250000, 500000,  1000000],
                "Page_Program_Latency_CSB" : [6250, 125000, 250000, 500000,  1000000],
                "Page_Program_Latency_MSB" : [6250, 125000,250000, 500000,  1000000],
                "Block_Erase_Latency" : [475000, 950000,1900000,3800000, 7600000],
                "Block_PR_Cycles_Limit" : [5000, 10000, 20000, 40000, 80000],
                "Suspend_Erase_Time" : [87500, 175000, 350000, 700000, 1400000],
                "Suspend_Program_time" : [25000, 50000, 100000, 200000, 400000],
                "Die_No_Per_Chip" : [8],
                "Plane_No_Per_Die" : [1],
                "Block_No_Per_Plane" : [512],
                "Page_No_Per_Block" : [512],
                "Page_Capacity" : [4096],
                "Page_Metadat_Capacity" : [56, 112, 224, 448, 896],
            },
        }
    }
}


working_set_ids = []
working_id2val = {}
id2name = []
# all the max confs
conf_max = []
conf_counter = 0

set_capacity = 256 * 1024 * 1024 * 1024

capacity_control_list = ["Flash_Channel_Count", "Chip_No_Per_Channel", "Die_No_Per_Chip", "Plane_No_Per_Die", "Block_No_Per_Plane","Page_No_Per_Block", "Page_Capacity"]
capacity_control_id = []
capacity_control_vals = []

size_controler = [["Queue_Fetch_Size", "GC_Hard_Threshold"],["IO_Queue_Depth", "GC_Exec_Threshold"]]
size_ids = [[],[]]
size_vals = [[],[]]

dummy_var_controler = ["Plane_Allocation_Scheme", "GC_Block_Selection_Policy", "Flash_Technology", "CMD_Suspension_Support"]
dummy_var_ids = []

base_conf = []
count = 0
confid2name = []              

for key in configuration_choices:
    print("ley is " + key)
    for key1 in configuration_choices[key]:
        for key2 in configuration_choices[key][key1]:
            if key2 != "Flash_Parameter_Set":
                confid2name.append(key2)
                conf_max.append(len(configuration_choices[key][key1][key2]))
                print(count)
                print(configuration_choices[key][key1][key2])
                print(configuration_base[key][key1][key2])
                base_conf.append(configuration_choices[key][key1][key2].index(configuration_base[key][key1][key2][0]))
                if conf_max[-1] > 1:
                    id2name.append(key2)
                    working_set_ids.append(conf_counter)
                    working_id2val[conf_counter] = configuration_choices[key][key1][key2]
                conf_counter += 1
                if key2 in capacity_control_list:
                    capacity_control_id.append(count)
                    capacity_control_vals.append(configuration_choices[key][key1][key2])
                if key2 in size_controler[0]:
                    size_ids[0].append(count)
                    size_vals[0].append(configuration_choices[key][key1][key2])
                if key2 in size_controler[1]:
                    size_ids[1].append(count)
                    size_vals[1].append(configuration_choices[key][key1][key2])
                if key2 in dummy_var_controler:
                    dummy_var_ids.append(count)
                count += 1
            else:
                for key3 in configuration_choices[key][key1][key2]:
                    confid2name.append(key3)
                    conf_max.append(len(configuration_choices[key][key1][key2][key3]))
                    print(count)
                    print(configuration_choices[key][key1][key2][key3])
                    print(configuration_base[key][key1][key2][key3])
                    base_conf.append(configuration_choices[key][key1][key2][key3].index(configuration_base[key][key1][key2][key3][0]))
                    if conf_max[-1] > 1:
                        id2name.append(key3)
                        working_set_ids.append(conf_counter)
                    conf_counter += 1
                    if key3 in capacity_control_list:
                        capacity_control_id.append(count)
                        capacity_control_vals.append(configuration_choices[key][key1][key2][key3])
                    if key3 in size_controler[0]:
                        size_ids[0].append(count)
                        size_vals[0].append(configuration_choices[key][key1][key2][key3])
                    if key3 in size_controler[1]:
                        size_ids[1].append(count)
                        size_vals[1].append(configuration_choices[key][key1][key2][key3])
                    if key3 in dummy_var_controler:
                        dummy_var_ids.append(count)
                    count += 1

def to_working_conf(conf):
    working_conf = []
    for i in range(0, len(conf_max)):
        if i in working_set_ids:
            if i in dummy_var_ids:
                for j in range(0, conf_max[i]):
                    if j == conf[i]:
                        working_conf.append(1.0)
                    else:
                        working_conf.append(0.0)
            else:
                working_conf.append(conf[i] / conf_max[i])
    return working_conf



def check_conf_ok(conf):
    return True

def run_cmd_old(cmd_string, timeout=1000):
    print("命令为：" + cmd_string)
    ata = os.popen(cmd_string)
    if (len(ata.read()) > 0):
        print ("succeed!")
    return


def get_next_conf(conf_prev, thisid):
    conf = conf_prev.copy()
    if thisid == -1:
        thisid = working_set_ids[0]
        conf[thisid] = 0
        return [conf, thisid]
    curindex = conf[thisid]
    print("DEBUGs::" + str(thisid) + ":" + str(conf[thisid]) + ", " + str(conf_max[thisid]))
    if curindex == conf_max[thisid] - 1:
        conf[thisid] = base_conf[thisid]
        cur = working_set_ids.index(thisid)
        if cur == len(working_set_ids) - 1:
            return [-1]
        else:
            thisid = working_set_ids[cur+1]
            conf[thisid] = 0
            return [conf, thisid] 
    else:
        conf[thisid] += 1
        return [conf, thisid] 


# if experiment_name not in os.listdir("../log"):
#     os.mkdir("../log/" + experiment_name)

# f_conf = open("../log/" + experiment_name + "/config_log-" + experiment_name, "a+")

# a common trace processing
# etest_traces = os.listdir("../test_traces")
# # tracedb maintain what is the current next trace to execute
# tracedb = {}
# for tracename in etest_traces:
#     cat = tracename.split("-")[0]
#     keys = tracename.split("-")
#     main_key = "-".join(keys[0:-1])
#     max_tracecount = int(keys[-1]) + 1
#     if cat not in tracedb:
#         tracedb[cat] = {}
#     if main_key not in tracedb[cat]:
#         tracedb[cat][main_key] = [0, {}]
#     if max_tracecount > tracedb[cat][main_key][0]:
#         tracedb[cat][main_key][0] = max_tracecount


id2conf = {}
newconf = np.zeros(len(conf_max), dtype=int)
crTable = {}
confs = []

# configuration to dict
def conf2dict(conf):
    # test configuration set
    counter = 0
    configuration = {}
    for key in configuration_choices:
        configuration[key] = dict()
        for key1 in configuration_choices[key]:
            configuration[key][key1] = dict()
            for key2 in configuration_choices[key][key1]:
                if key2 != "Flash_Parameter_Set":
                    configuration[key][key1][key2] = configuration_choices[key][key1][key2][conf[counter]]
                    counter += 1
                else:
                    configuration[key][key1][key2] = dict()
                    for key3 in configuration_choices[key][key1][key2]:
                        configuration[key][key1][key2][key3] = configuration_choices[key][key1][key2][key3][conf[counter]]
                        counter += 1
    if conf[size_ids[0][0]] != base_conf[size_ids[0][0]]:
        configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["IO_Queue_Depth"] = configuration["Execution_Parameter_Set"]["Device_Parameter_Set"]["Queue_Fetch_Size"]
    return configuration



import random
def run_trace(confid, tracename, input_filename, output_filename):
    # print("in run trace")
    current_max_conf = confs[confid]
    tconf = conf2dict(current_max_conf)
    random_state = random.randint(0, 1e6)
    save_conf(tconf, "../log/" + experiment_name + "/"+ experiment_name +"test_conf" + str(confs.index(current_max_conf)) + ".xml", random_state)
    save_workload(tconf, "../test_traces/" + tracename , "../log/" + experiment_name + "/"+ experiment_name +"test_workload" + str(confid) + "-" + tracename + ".xml", input_filename, output_filename)
    print("Perform: "+"conf " + str(confid) +" -> " + tracename)
    cmd = "timeout 6000 ../MQSim/MQSim -i ../log/"+ experiment_name + "/"+ experiment_name +"test_conf"+ str(confid) + ".xml"+" -w ../log/"+ experiment_name + "/" + experiment_name +"test_workload"+ str(confid) + "-" + tracename + ".xml"
    if (experiment_name + "test_workload"+ str(confid) + "-" + tracename +"_scenario_1.xml") not in os.listdir("../log/" + experiment_name + ""):
        run_cmd_old(cmd, timeout=100000000)
    else:
        print("result existing.......")
    result = [-1, -1, -1, -1, -1]
    if (experiment_name + "test_workload"+ str(confid) + "-" + tracename +"_scenario_1.xml") in os.listdir("../log/" + experiment_name + ""):
        result = get_performance("../log/" + experiment_name + "/"+ experiment_name +"test_workload"+ str(confid) + "-" + tracename +"_scenario_1.xml")
        # print(result)
        if result[5] != result[6]:
            return [-1, -1, -1, -1, -1]
        result = result[0:5]
        if tracename in crTable:
            if confid in crTable[tracename]:
                crTable[tracename][confid].append(result)
            else:
                crTable[tracename][confid] = [result]
        else: 
            crTable[tracename] = {
                confid : [result],
            }
        print("* Result: lat = " + str(result[0]) + ", thpt = " + str(result[4]))
    else:
        print("! Failed")
        if tracename in crTable:
            crTable[tracename][confid] = [[-1,-1,-1,-1,-1]]
        else:
            crTable[tracename] = {
                confid: [[-1,-1,-1,-1,-1]],
            }
    return result

def prepare_and_get_tracenames(cat, confid, cache_size, page_size):
    all_names = []
    count = 1
    for main_key in tracedb[cat]:
        total_num = tracedb[cat][main_key][0]
        if main_key + "-0-" + str(cache_size) + "-" + str(page_size) not in tracedb[cat][main_key][1]:
            tracedb[cat][main_key][1][main_key + "-0-" + str(cache_size) + "-" + str(page_size)] = 0
            run_trace(confid, main_key + "-0","", "../cache_warmup_dat/" + main_key + "-0-" + experiment_name + "-" + str(cache_size)  + "-" + str(page_size))
        all_names.append([main_key + "-1", "../cache_warmup_dat/" + main_key + "-0-" + experiment_name + "-" + str(cache_size) + "-" + str(page_size), "../cache_warmup_dat/" + main_key + "-1-" + experiment_name + "-" + str(cache_size)+ "-" + str(page_size)])
        if len(all_names) >= count:
            return all_names
    return all_names

# trace_dir = "../test_traces/"
f = open("../xdb/coarsed_pruning/" + "confid2name.dat", "w+")
f.write(json.dumps(confid2name))
f.close()

traces = []
traces += [f"LiveMapsBackEnd-1-0-{i}" for i in range(8, 10)]
traces += [f"YCSB-0-0-{i}" for i in range(2, 3)]
traces += [f"TPCC-{i}-0-0" for i in range(1, 2)]
traces += [f"MapReduce-{i}-0-0" for i in range(1, 2)]
traces += [f"AdspayLoad-0-0-{i}" for i in range(2, 3)]
traces += [f"CloudStorage-{i}-0-0" for i in range(6, 7)]
traces += [f"WebSearch-{i}-0-0" for i in range(1, 2)]

newconf = [base_conf.copy(), -1]
while newconf[0] != -1:
    if newconf[0] in confs:
        confid = confs.index(newconf[0])
    else:
        confs.append(newconf[0])
        # f_conf.write(json.dumps(newconf[0]))
        tconf = conf2dict_pruning(newconf[0], newconf[1])
        confid = len(confs) - 1
    print("generated valid confid:" + str(confid))
    t_conf = conf2dict(newconf[0])
    cache_size = t_conf["Execution_Parameter_Set"]["Device_Parameter_Set"]["Data_Cache_Capacity"]
    page_size = t_conf["Execution_Parameter_Set"]["Device_Parameter_Set"]["Flash_Parameter_Set"]["Page_Capacity"]
    random_state = random.randint(0, 1e6)
    save_conf(tconf, "../xdb/coarsed_pruning/configurations/"+ str(confid) +".xml", random_state)
    # save_workload(tconf, "../xdb/coarsed_pruning/workloads/"+ str(confid) + "-" + tracename + ".xml", input_filename, output_filename)
    # tracenames = prepare_and_get_tracenames(perf_cat, confid, cache_size, page_size)
    # for tracename in tracenames:
    #     result = run_trace(confid, tracename[0], tracename[1], tracename[2])
    newconf = get_next_conf(newconf[0], newconf[1])
    confs = np.array(confs).tolist()
    f = open("../xdb/coarsed_pruning/" + "confs.dat", "w+")
    f.write(json.dumps(confs))
    f.close()
