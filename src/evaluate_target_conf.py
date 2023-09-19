import os
import subprocess
import xml
import xml.dom.minidom
import time
import math
import json


def store_trace(dir, io_vec):
    f = open(dir, "w")
    for io in io_vec:
        for i in range(0, len(io)):
            io[i] = str(io[i])
        f.write(" ".join(io))
    f.close()

# Run Given Shell Command
def run_shell_cmd(cmd_string, timeout=1000000):
    print("Executing Shell Command:" + cmd_string)
    ata = os.popen(cmd_string)
    if (len(ata.read()) > 0):
        print("succeed!")
    return

id_for_priorities = {
    "URGENT" : 0,
    "HIGH" : 1,
    "MEDIUM" : 2,
    "LOW" : 3
}

# Getting performance metrics from XML result file
# Input: fname = the filename of performance xml
# Output: [latency, e2e_latency, tail_latency, e2e_tail_latency, throughput, request_generarted, request_served], 
#         return None if nothing in the file.
def get_performance_from_xml(fname):
    try:
        DOMTree = xml.dom.minidom.parse(fname)
    except:
        print(f"evaluating configuration {fname} failed")
        return None
    collection = DOMTree.documentElement
    results = collection.getElementsByTagName("Host")[0]
    results = results.getElementsByTagName("Host.IO_Flow")[0]
    elatency = results.getElementsByTagName("Device_Response_Time")[0]
    emaxlatency = results.getElementsByTagName("Max_Device_Response_Time")[0]
    eteRes = results.getElementsByTagName("End_to_End_Request_Delay")[0]
    maxeteRes = results.getElementsByTagName("Max_End_to_End_Request_Delay")[0]
    bandwidth = results.getElementsByTagName("Bandwidth")[0]
    ReqGen = results.getElementsByTagName("Request_Count")[0]
    ReqServ = results.getElementsByTagName("Serviced_Request_Count")[0]
    # get the channel utilization
    ssd_device_results = collection.getElementsByTagName("SSDDevice")[0]
    ssd_device_results = ssd_device_results.getElementsByTagName("SSDDevice.TSU")[0]
    ssd_queue_length_by_chip = {}
    # average queue length, std_dev queue length, average wait time, max wait time 
    for key in id_for_priorities:
        for element in ssd_device_results.getElementsByTagName(f"SSDDevice.TSU.User_Read_TR_Queue.Priority.{key}"):
            name = element.attributes["Name"].nodeValue
            io_type = name.split("_")[1]
            channel = name.split("@")[1]
            chip = name.split("@")[2]
            priority = name.split("@")[3]
            average_queue_length = float(element.attributes["Avg_Queue_Length"].nodeValue)
            std_queue_length = float(element.attributes["STDev_Queue_Length"].nodeValue)
            avg_wait_time = 0
            if average_queue_length != 0:
                avg_wait_time = int(element.attributes["Avg_Transaction_Waiting_Time"].nodeValue)
            if io_type not in ssd_queue_length_by_chip:
                ssd_queue_length_by_chip[io_type] = {}
            # construct the dictionary
            if channel not in ssd_queue_length_by_chip[io_type]:
                ssd_queue_length_by_chip[io_type][channel] = {}
            if chip not in ssd_queue_length_by_chip[io_type][channel]:
                ssd_queue_length_by_chip[io_type][channel][chip] = [[], [], [], []]
            ssd_queue_length_by_chip[io_type][channel][chip][id_for_priorities[priority]] = [average_queue_length, std_queue_length, avg_wait_time]
    return [float(elatency.childNodes[0].data), float(emaxlatency.childNodes[0].data),
            float(eteRes.childNodes[0].data), float(maxeteRes.childNodes[0].data),float(bandwidth.childNodes[0].data), int(ReqGen.childNodes[0].data), int(ReqServ.childNodes[0].data),
            ssd_queue_length_by_chip]


Device_Throughput_Dict = {
    "TPCC" : 0.0328125,
    "YCSB" : 1.953125,
    "TPCCTest" : 0.0328125,
    "YCSBTest" : 1.953125,
    "CloudStorageTest" : 0.14980120014783002,
    "MapReduce" : 0.07060245147500041,
    "AdspayLoad" : 0.035565352752920026,
    "CloudStorage" : 0.14980120014783002,
    "WebSearch" : 0.004149089825138838,
    "LiveMapsBackEnd" : 0.15190748401951898,
    "VDI" : 0.36310830064441446,
    "DevTool" : 0.062142572641788144,
    "MSN" : 0.1459765460669718,
    "MLPrep" : 1.3698391678548854,
    "FIUHome" : 0.07911744667194373,
    "PageRank" : 1.4154919003129869,
    "RadiusAuth" : 0.08398415552636936
}

Best_QueueDepth_Dict = {
    "TPCCTest" : 32,
    "YCSBTest" : 4,
    "CloudStorageTest" : 4,
    "TPCC" : 32,
    "YCSB" : 4,
    "MapReduce" : 256,
    "AdspayLoad" : 16,
    "CloudStorage" : 4,
    "WebSearch" : 256,
    "LiveMapsBackEnd" : 16,
    "MSN" : 256,
    "VDI" : 32,
    "DevTool" : 32,
    "MLPrep" : 32,
    "FIUHome" : 4,
    "PageRank" : 256,
    "RadiusAuth" : 32
}

# Save Workload Spec to Given Filename
# Input: trace filename, target save filename, input cache file name, output cache filename, layout conf ([channel chip die plane])
def save_workload_to_file(trace_dir, filename, input_filename, output_filename, conf, output_dram_file=None):
    channel_num = conf[0]
    chip_num = conf[1]
    die_num = conf[2]
    plane_num = conf[3]
    exec_perc = 100
    workload_type = trace_dir.split("/")[-1].split("-")[0]
    throughput = ""
    if workload_type in Device_Throughput_Dict:
        throughput = str(Device_Throughput_Dict[workload_type])
    best_queue_size = ""
    if workload_type in Best_QueueDepth_Dict:
        best_queue_size = Best_QueueDepth_Dict[workload_type]
    dram_output_filename = ""
    if output_dram_file:
        dram_output_filename = output_dram_file
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
                            <Initial_Occupancy_Percentage>50</Initial_Occupancy_Percentage>
                            <Cache_Input_Filename>{}</Cache_Input_Filename>
                            <Cache_Output_Filename>{}</Cache_Output_Filename>
                            <Device_Throughput>{}</Device_Throughput>
                            <File_Path>{}</File_Path>
                            <Percentage_To_Be_Executed>{}</Percentage_To_Be_Executed>
                            <Best_Queue_Size>{}</Best_Queue_Size>
                            <Dram_Output_Filename>{}</Dram_Output_Filename>
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
                                    throughput,
                                    trace_dir, 
                                    exec_perc,
                                    best_queue_size,
                                    dram_output_filename)
    f = open(filename, "w")
    f.write(workload_str)
    f.close()

# Save Workload Spec to Given Filename
# Input: trace filename, target save filename, input cache file name, output cache filename, layout conf ([channel chip die plane])
def save_workload_to_file_with_queue_size(trace_dir, filename, input_filename, output_filename, conf, queue_size):
    channel_num = conf[0]
    chip_num = conf[1]
    die_num = conf[2]
    plane_num = conf[3]
    exec_perc = 100
    workload_type = trace_dir.split("/")[-1].split("-")[0]
    throughput = ""
    if workload_type in Device_Throughput_Dict:
        throughput = str(Device_Throughput_Dict[workload_type])
    best_queue_size = queue_size
    # if workload_type in Best_QueueDepth_Dict:
    #     best_queue_size = Best_QueueDepth_Dict[workload_type]
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
                            <Initial_Occupancy_Percentage>50</Initial_Occupancy_Percentage>
                            <Cache_Input_Filename>{}</Cache_Input_Filename>
                            <Cache_Output_Filename>{}</Cache_Output_Filename>
                            <Device_Throughput>{}</Device_Throughput>
                            <File_Path>{}</File_Path>
                            <Percentage_To_Be_Executed>{}</Percentage_To_Be_Executed>
                            <Best_Queue_Size>{}</Best_Queue_Size>
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
                                    throughput,
                                    trace_dir,
                                    exec_perc,
                                    best_queue_size)
    f = open(filename, "w")
    f.write(workload_str)
    f.close()


import random

# Input: conf_name: str, workload_name: str
# Output: [latency, e2e_latency, tail_latency, e2e_tail_latency, throughput], all -1 if execution failed.
def run_trace(conf_name, workload_name):
    workload_dir = "/".join(workload_name.split("/")[0:-1])
    workload_prefix = ".".join((workload_name.split("/")[-1]).split(".")[0:-1])
    rand = random.random()
    cmd = "timeout 6000 ../MQSim/MQSim -i " + conf_name + " -w " + workload_name + " >" + workload_prefix + f"{rand}.log" 
    if (workload_prefix + "_scenario_1.xml") not in os.listdir(workload_dir):
        run_shell_cmd(cmd, timeout=100000000)
        cmd = f"rm " + workload_prefix + f"{rand}.log"
        run_shell_cmd(cmd, timeout=100000000)
    result = None
    # WARNING: ONLY WORK ON LINUX SYSTEMS
    if (workload_prefix + "_scenario_1.xml") in os.listdir(workload_dir):
        result = get_performance_from_xml(workload_dir + "/" + workload_prefix + "_scenario_1.xml")
        if not result:
            return None
        result = result[0:5]
    else:
        result = None
    if result:
        print(f"*** Run Trace: {conf_name} on {workload_name} \n* Result: average latency = " + str(result[0]) + ", average throughput = " + str(result[4]))
    return result

# Input: conf_name: str, workload_name: str
# Output: [latency, e2e_latency, tail_latency, e2e_tail_latency, throughput], all -1 if execution failed.
def run_trace_nonstop(conf_name, workload_name):
    workload_dir = "/".join(workload_name.split("/")[0:-1])
    workload_prefix = ".".join((workload_name.split("/")[-1]).split(".")[0:-1])
    rand = random.random()
    cmd = "timeout 6000 ../MQSim/MQSim -i " + conf_name + " -w " + workload_name + " >" + workload_prefix + f"{rand}.log" 
    if (workload_prefix + "_scenario_1.xml") not in os.listdir(workload_dir):
        # run_shell_cmd(cmd, timeout=100000000)
        cmd = f"rm " + workload_prefix + f"{rand}.log"
        # run_shell_cmd(cmd, timeout=100000000)
    result = None
    # WARNING: ONLY WORK ON LINUX SYSTEMS
    if (workload_prefix + "_scenario_1.xml") in os.listdir(workload_dir):
        result = get_performance_from_xml(workload_dir + "/" + workload_prefix + "_scenario_1.xml")
        if not result:
            return None
        result = result[0:5]
    else:
        result = None
    if result:
        print(f"*** Run Trace: {conf_name} on {workload_name} \n* Result: average latency = " + str(result[0]) + ", average throughput = " + str(result[4]))
    return result

# Input: conf_name: str, workload_name: str
# Output: [latency, e2e_latency, tail_latency, e2e_tail_latency, throughput], all -1 if execution failed.
def generate_run_trace(conf_name, workload_name):
    workload_dir = "/".join(workload_name.split("/")[0:-1])
    workload_prefix = ".".join((workload_name.split("/")[-1]).split(".")[0:-1])
    rand = random.random()
    cmd = "../MQSim/MQSim -i " + conf_name + " -w " + workload_name + " >" + workload_prefix + f"{rand}.log" 
    if (workload_prefix + "_scenario_1.xml") not in os.listdir(workload_dir):
        cmd1 = f"rm " + workload_prefix + f"{rand}.log"
        return [cmd, cmd1, workload_dir + "/" + workload_prefix + "_scenario_1.xml"]
    else:
        f = open(workload_dir + "/" + workload_prefix + "_scenario_1.xml", "r")
        a = len(f.read())
        if a == 0:
            cmd1 = f"rm " + workload_prefix + f"{rand}.log"
            return [cmd, cmd1, workload_dir + "/" + workload_prefix + "_scenario_1.xml"]
        return None

def save_to_xdb(results, conf_id, trace_id, db_dir):
    if not results:
        print(f"ERROR: Trace Execution Error! {conf_id} {trace_id}")
        return None
    crTableFilename = db_dir  + "/crTable.json"
    crTable = {}
    if "crTable.json" not in os.listdir(db_dir):
        crTable = {}
    else:
        crTablefp = open(crTableFilename, "r")
        crTable = json.loads(crTablefp.read())
        crTablefp.close()
    if conf_id not in crTable:
        crTable[conf_id] = {}
    if trace_id not in crTable[conf_id]:
        crTable[conf_id][trace_id] = []
    crTable[conf_id][trace_id].append(results)
    crTablefp = open(crTableFilename, "w")
    crTablefp.write(json.dumps(crTable))
    crTablefp.close()

# Input: Configuration File Path, Trace File Path
# Output: Performance of Given Configuration on Given Workload. If Error happens, return None.
# Guarantee: The configuration-performance pair is stored in XDB
def evaluate_config_workload(conf_name, trace_name):
    # first identify the layout and stable configurations (NVME/SATA, MLC/SLC) of conf_name
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
    interface = device_results.getElementsByTagName("HostInterface_Type")[0]
    flash_parameters = device_results.getElementsByTagName("Flash_Parameter_Set")[0]
    technology = flash_parameters.getElementsByTagName("Flash_Technology")[0]
    channel = device_results.getElementsByTagName("Flash_Channel_Count")[0]
    chip = device_results.getElementsByTagName("Chip_No_Per_Channel")[0]
    cache_size = device_results.getElementsByTagName("Data_Cache_Capacity")[0]
    die = flash_parameters.getElementsByTagName("Die_No_Per_Chip")[0]
    plane = flash_parameters.getElementsByTagName("Plane_No_Per_Die")[0]
    # Check whether the configuration is in XDB. If not, abandon this execution.
    # We can only launch experiments with configurations that is already in XDB
    db_table_name = str(interface.childNodes[0].data).lower() + "_" + str(technology.childNodes[0].data).lower()
    conf_prefix = "/".join(conf_name.split("/")[0:-1])
    # if not conf_prefix.endswith(db_table_name + "/configurations"):
    #     print("ERROR: Configuration not located in target folder.")
    #     print(conf_prefix)
    #     print(db_table_name)
    #     return None
    layout = []
    layout.append(int(channel.childNodes[0].data))
    layout.append(int(chip.childNodes[0].data))
    layout.append(int(die.childNodes[0].data))
    layout.append(int(plane.childNodes[0].data))
    # TODO you can add custom constraints here
    # then, identify the warmup file, if not present, perform warmup and generate warmup file
    # reminder: we use the same warmup file for each trace type(eg. TPCC).
    db_dir = "/".join(conf_name.split("/")[0:-2])
    trace_dir = "/".join(trace_name.split("/")[0:-1])
    trace_id = trace_name.split("/")[-1]
    conf_id = ".".join(conf_name.split("/")[-1].split(".")[0:-1])
    category = trace_name.split("/")[-1].split("-")[0]
    warmup_filename = category + "-0-0-0-" + str(cache_size.childNodes[0].data)
    warmup_dir = db_dir + "/warmup" 
    dram_trace_dir = db_dir + "/dram_trace"
    dram_filename = conf_id + "_" + trace_id + ".dramtrace"
    warmup_tracename = trace_dir + "/" + category + "-0-0-0"
    if warmup_filename not in os.listdir(warmup_dir):
        print(f"WARMUP SNAPSHOT NOT FOUND. WARMING UP DEVICE FOR {warmup_filename}")
        save_workload_to_file(warmup_tracename, db_dir + "/workloads/" + f"{conf_id}_{category}-0-0-0.xml", "", warmup_dir + "/" + warmup_filename, layout)
        run_trace(conf_name, db_dir + "/workloads/" + f"{conf_id}_{category}-0-0-0.xml")
        if warmup_filename not in os.listdir(warmup_dir):
            print("ERROR: Warmup trace cannot be performed.")
            return None
    # then, generate and save the workload file.
    save_workload_to_file(trace_name, db_dir + "/workloads/" + f"{conf_id}_{trace_id}.xml",  warmup_dir + "/" + warmup_filename, "", layout, dram_trace_dir + "/" + dram_filename)
    # then, perform configuration evaluation.
    results = run_trace(conf_name, db_dir + "/workloads/" + f"{conf_id}_{trace_id}.xml")
    # last, save config-workload pair to XDB.
    save_to_xdb(results, conf_id, trace_id, db_dir)
    return results

# Input: Configuration File Path, Trace File Path
# Output: Performance of Given Configuration on Given Workload. If Error happens, return None.
# Guarantee: The configuration-performance pair is stored in XDB
def evaluate_config_workload_nonstop(conf_name, trace_name):
    # first identify the layout and stable configurations (NVME/SATA, MLC/SLC) of conf_name
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
    interface = device_results.getElementsByTagName("HostInterface_Type")[0]
    flash_parameters = device_results.getElementsByTagName("Flash_Parameter_Set")[0]
    technology = flash_parameters.getElementsByTagName("Flash_Technology")[0]
    channel = device_results.getElementsByTagName("Flash_Channel_Count")[0]
    chip = device_results.getElementsByTagName("Chip_No_Per_Channel")[0]
    cache_size = device_results.getElementsByTagName("Data_Cache_Capacity")[0]
    die = flash_parameters.getElementsByTagName("Die_No_Per_Chip")[0]
    plane = flash_parameters.getElementsByTagName("Plane_No_Per_Die")[0]
    # Check whether the configuration is in XDB. If not, abandon this execution.
    # We can only launch experiments with configurations that is already in XDB
    db_table_name = str(interface.childNodes[0].data).lower() + "_" + str(technology.childNodes[0].data).lower()
    conf_prefix = "/".join(conf_name.split("/")[0:-1])
    # if not conf_prefix.endswith(db_table_name + "/configurations"):
    #     print("ERROR: Configuration not located in target folder.")
    #     print(conf_prefix)
    #     print(db_table_name)
    #     return None
    layout = []
    layout.append(int(channel.childNodes[0].data))
    layout.append(int(chip.childNodes[0].data))
    layout.append(int(die.childNodes[0].data))
    layout.append(int(plane.childNodes[0].data))
    # TODO you can add custom constraints here
    # then, identify the warmup file, if not present, perform warmup and generate warmup file
    # reminder: we use the same warmup file for each trace type(eg. TPCC).
    db_dir = "/".join(conf_name.split("/")[0:-2])
    trace_dir = "/".join(trace_name.split("/")[0:-1])
    trace_id = trace_name.split("/")[-1]
    conf_id = ".".join(conf_name.split("/")[-1].split(".")[0:-1])
    category = trace_name.split("/")[-1].split("-")[0]
    warmup_filename = category + "-0-0-0-" + str(cache_size.childNodes[0].data)
    warmup_dir = db_dir + "/warmup" 
    dram_trace_dir = db_dir + "/dram_trace"
    dram_filename = conf_id + "_" + trace_id + ".dramtrace"
    warmup_tracename = trace_dir + "/" + category + "-0-0-0"
    if warmup_filename not in os.listdir(warmup_dir):
        print(f"WARMUP SNAPSHOT NOT FOUND. WARMING UP DEVICE FOR {warmup_filename}")
        save_workload_to_file(warmup_tracename, db_dir + "/workloads/" + f"{conf_id}_{category}-0-0-0.xml", "", warmup_dir + "/" + warmup_filename, layout)
        # run_trace(conf_name, db_dir + "/workloads/" + f"{conf_id}_{category}-0-0-0.xml")
        if warmup_filename not in os.listdir(warmup_dir):
            print("ERROR: Warmup trace cannot be performed.")
            return None
    # then, generate and save the workload file.
    save_workload_to_file(trace_name, db_dir + "/workloads/" + f"{conf_id}_{trace_id}.xml",  warmup_dir + "/" + warmup_filename, "", layout, dram_trace_dir + "/" + dram_filename)
    # then, perform configuration evaluation.
    results = run_trace_nonstop(conf_name, db_dir + "/workloads/" + f"{conf_id}_{trace_id}.xml")
    # last, save config-workload pair to XDB.
    save_to_xdb(results, conf_id, trace_id, db_dir)
    return results

# Input: Configuration File Path, Trace File Path
# Output: Performance of Given Configuration on Given Workload. If Error happens, return None.
# Guarantee: The configuration-performance pair is stored in XDB
def generate_config_workload(conf_name, trace_name, trace_dram=False):
    # first identify the layout and stable configurations (NVME/SATA, MLC/SLC) of conf_name
    commands = []
    print(conf_name)
    DOMTree = xml.dom.minidom.parse(conf_name)
    if not DOMTree:
        print("ERROR: Configuration File Not Found")
        return None
    collection = DOMTree.documentElement
    results = collection
    host_results = results.getElementsByTagName("Host_Parameter_Set")[0]
    device_results = results.getElementsByTagName("Device_Parameter_Set")[0]
    interface = device_results.getElementsByTagName("HostInterface_Type")[0]
    flash_parameters = device_results.getElementsByTagName("Flash_Parameter_Set")[0]
    technology = flash_parameters.getElementsByTagName("Flash_Technology")[0]
    channel = device_results.getElementsByTagName("Flash_Channel_Count")[0]
    chip = device_results.getElementsByTagName("Chip_No_Per_Channel")[0]
    cache_size = device_results.getElementsByTagName("Data_Cache_Capacity")[0]
    die = flash_parameters.getElementsByTagName("Die_No_Per_Chip")[0]
    plane = flash_parameters.getElementsByTagName("Plane_No_Per_Die")[0]
    # Check whether the configuration is in XDB. If not, abandon this execution.
    # We can only launch experiments with configurations that is already in XDB
    db_table_name = str(interface.childNodes[0].data).lower() + "_" + str(technology.childNodes[0].data).lower()
    conf_prefix = "/".join(conf_name.split("/")[0:-1])
    # if not conf_prefix.endswith(db_table_name + "/configurations"):
    #     print("ERROR: Configuration not located in target folder.")
    #     print(conf_prefix)
    #     print(db_table_name + "/configurations")
    #     return None
    layout = []
    layout.append(int(channel.childNodes[0].data))
    layout.append(int(chip.childNodes[0].data))
    layout.append(int(die.childNodes[0].data))
    layout.append(int(plane.childNodes[0].data))
    # TODO you can add custom constraints here
    # then, identify the warmup file, if not present, perform warmup and generate warmup file
    # reminder: we use the same warmup file for each trace type(eg. TPCC).
    db_dir = "/".join(conf_name.split("/")[0:-2])
    trace_dir = "/".join(trace_name.split("/")[0:-1])
    trace_id = trace_name.split("/")[-1]
    conf_id = ".".join(conf_name.split("/")[-1].split(".")[0:-1])
    category = trace_name.split("/")[-1].split("-")[0]
    warmup_filename = category + "-0-0-0-" + str(cache_size.childNodes[0].data)
    warmup_dir = db_dir + "/warmup" 
    warmup_tracename = trace_dir + "/" + category + "-0-0-0"
    dram_trace_dir=""
    dram_filename=""
    if trace_dram:
        dram_trace_dir = db_dir + "/dram_trace"
        dram_filename = conf_id + "_" + trace_id + ".dramtrace"
    if warmup_filename not in os.listdir(warmup_dir):
        print(f"WARMUP SNAPSHOT NOT FOUND. WARMING UP DEVICE FOR {warmup_filename}")
        save_workload_to_file(warmup_tracename, db_dir + "/workloads/" + f"{conf_id}_{category}-0-0-0.xml", "", warmup_dir + "/" + warmup_filename, layout)
        cmds1 = generate_run_trace(conf_name, db_dir + "/workloads/" + f"{conf_id}_{category}-0-0-0.xml")
        if cmds1:
            commands.append(cmds1)
    # then, generate and save the workload file.
    if trace_dram:
        save_workload_to_file(trace_name, db_dir + "/workloads/" + f"{conf_id}_{trace_id}.xml",  warmup_dir + "/" + warmup_filename, "", layout, dram_trace_dir + "/" + dram_filename)
    else:
        save_workload_to_file(trace_name, db_dir + "/workloads/" + f"{conf_id}_{trace_id}.xml",  warmup_dir + "/" + warmup_filename, "", layout, "")
    # then, perform configuration evaluation.
    cmds2 = generate_run_trace(conf_name, db_dir + "/workloads/" + f"{conf_id}_{trace_id}.xml")
    if cmds2:
        cmds2.append([conf_id, trace_id, db_dir])
        commands.append(cmds2)
    return commands

# Input: Configuration File Path, Trace File Path
# Output: Performance of Given Configuration on Given Workload. If Error happens, return None.
# Guarantee: The configuration-performance pair is stored in XDB
def generate_queuetest_config_workload(conf_name, trace_name, queue_size):
    # first identify the layout and stable configurations (NVME/SATA, MLC/SLC) of conf_name
    commands = []
    DOMTree = xml.dom.minidom.parse(conf_name)
    if not DOMTree:
        print("ERROR: Configuration File Not Found")
        return None
    collection = DOMTree.documentElement
    results = collection
    host_results = results.getElementsByTagName("Host_Parameter_Set")[0]
    device_results = results.getElementsByTagName("Device_Parameter_Set")[0]
    interface = device_results.getElementsByTagName("HostInterface_Type")[0]
    flash_parameters = device_results.getElementsByTagName("Flash_Parameter_Set")[0]
    technology = flash_parameters.getElementsByTagName("Flash_Technology")[0]
    channel = device_results.getElementsByTagName("Flash_Channel_Count")[0]
    chip = device_results.getElementsByTagName("Chip_No_Per_Channel")[0]
    cache_size = device_results.getElementsByTagName("Data_Cache_Capacity")[0]
    die = flash_parameters.getElementsByTagName("Die_No_Per_Chip")[0]
    plane = flash_parameters.getElementsByTagName("Plane_No_Per_Die")[0]
    # Check whether the configuration is in XDB. If not, abandon this execution.
    # We can only launch experiments with configurations that is already in XDB
    db_table_name = str(interface.childNodes[0].data).lower() + "_" + str(technology.childNodes[0].data).lower()
    conf_prefix = "/".join(conf_name.split("/")[0:-1])
    # if not conf_prefix.endswith(db_table_name + "/configurations"):
    #     print("ERROR: Configuration not located in target folder.")
    #     return None
    layout = []
    layout.append(int(channel.childNodes[0].data))
    layout.append(int(chip.childNodes[0].data))
    layout.append(int(die.childNodes[0].data))
    layout.append(int(plane.childNodes[0].data))
    # TODO you can add custom constraints here
    # then, identify the warmup file, if not present, perform warmup and generate warmup file
    # reminder: we use the same warmup file for each trace type(eg. TPCC).
    db_dir = "/".join(conf_name.split("/")[0:-2])
    trace_dir = "/".join(trace_name.split("/")[0:-1])
    trace_id = trace_name.split("/")[-1]
    conf_id = ".".join(conf_name.split("/")[-1].split(".")[0:-1])
    category = trace_name.split("/")[-1].split("-")[0]
    warmup_filename = category + "-0-0-0-" + str(cache_size.childNodes[0].data)
    warmup_dir = db_dir + "/warmup" 
    warmup_tracename = trace_dir + "/" + category + "-0-0-0"
    if warmup_filename not in os.listdir(warmup_dir):
        print(f"WARMUP SNAPSHOT NOT FOUND. WARMING UP DEVICE FOR {warmup_filename}")
        save_workload_to_file_with_queue_size(warmup_tracename, db_dir + "/workloads/" + f"{conf_id}_{category}-0-0-0.xml", "", warmup_dir + "/" + warmup_filename, layout, 4)
        cmds1 = generate_run_trace(conf_name, db_dir + "/workloads/" + f"{conf_id}_{category}-0-0-0.xml")
        if cmds1:
            commands.append(cmds1)
    # then, generate and save the workload file.
    save_workload_to_file_with_queue_size(trace_name, db_dir + "/workloads/" + f"{conf_id}_{trace_id}.xml",  warmup_dir + "/" + warmup_filename, "", layout, queue_size)
    # then, perform configuration evaluation.
    cmds2 = generate_run_trace(conf_name, db_dir + "/workloads/" + f"{conf_id}_{trace_id}.xml")
    if cmds2:
        cmds2.append([conf_id, trace_id, db_dir])
        commands.append(cmds2)
    return commands


Ereadbit = 0.15
Ewritebit = 3.31
Eerasebit = 0.07    
PIdle = 12.7
P_ARM = 2000
# optimal workloads

def get_performance_energy(fname):
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
    results = collection.getElementsByTagName("SSDDevice")[0]
    results = results.getElementsByTagName("SSDDevice.FlashChips")
    chipdata = []
    for chipinfo in results:
        if chipinfo.getAttribute("ID") != "":
            # print(chipinfo.getAttribute("Time_in_Idle"))
            chipdata.append([chipinfo.getAttribute("ID"), float(chipinfo.getAttribute("Time_in_Idle")), float(chipinfo.getAttribute("Read_count")), float(chipinfo.getAttribute("Program_count")),  float(chipinfo.getAttribute("Erase_count")) , float(chipinfo.getAttribute("Fraction_of_Time_in_Execution")),  float(chipinfo.getAttribute("Fraction_of_Time_in_DataXfer"))])
    print(chipdata)
    return [float(elatency.childNodes[0].data), float(emaxlatency.childNodes[0].data),
            float(eteRes.childNodes[0].data), float(maxeteRes.childNodes[0].data),float(ioPS.childNodes[0].data), int(ReqGen.childNodes[0].data), int(ReqServ.childNodes[0].data), chipdata]

def get_energy_conf_workload(conf_name,  trace_name, pagesize, blocksize, dram_power):
    trace_id = trace_name.split("/")[-1]
    conf_id = ".".join(conf_name.split("/")[-1].split(".")[0:-1])
    db_dir = "/".join(conf_name.split("/")[0:-2])
    if (f"{conf_id}_{trace_id}" +"_scenario_1.xml") in os.listdir(db_dir + "/workloads/"):
        result = get_performance_energy(db_dir + "/workloads/" + f"{conf_id}_{trace_id}" +"_scenario_1.xml")
        # result[4] *= thpt_factor
        chipdata  = result[7]
        energy_chip = 0.0
        exec_time = 0
        for data in chipdata:
            exec_time = float(data[1]) / (1 -  float(data[5]) - float(data[6]))
            energy_chip += float(data[1]) * PIdle * (1e-9) + (float(data[2]) * pagesize * 8 * Ereadbit + float(data[3]) * pagesize * 8* Ewritebit + float(data[4]) * blocksize * 8 * Eerasebit) * 1e-6
        energy_dram = 0
        energy_dram = exec_time * dram_power * (1e-9) 
        # energy_dram = get_drampower(dramtrace_filename)
        energy_arm = exec_time * P_ARM * (1e-9) 
        return [energy_chip, energy_dram, energy_arm]

# baseline_DRAM = {
#     "AdspayLoad" : 71.59,
#     "YCSB" : 84.81,
#     "TPCC" : 62.30,
#     "WebSearch" : 58.59,
#     "MapReduce" : 92.75,
#     "CloudStorage" : 57.78,
#     "LiveMapsBackEnd" : 92.13
# }

# optimized_DRAM = {
#     "AdspayLoad" : 54.3,
#     "YCSB" : 105.47,
#     "TPCC" : 58.6,
#     "WebSearch" : 78.96,
#     "MapReduce" : 112,
#     "CloudStorage" : 57.89,
#     "LiveMapsBackEnd" : 79.59
# }


# conf2trace = {
#     "RC3" : "AdspayLoad",
#     "KV" : "YCSB",
#     "DB" : "TPCC",
#     "WS11" : "WebSearch",
#     "CS10" : "MapReduce",
#     "CS2" : "CloudStorage",
#     "MR" : "LiveMapsBackEnd"
# }

# conf2block = {
#     "baseline" : 512,
#     "RC3" : 256,
#     "KV" : 512,
#     "DB" : 512,
#     "WS11" : 512,
#     "CS10" : 256,
#     "CS2" : 256,
#     "MR" : 768 
# }

# baseline_dict = {}
# optimized_dict = {}

# for confn in confnames:
#     for tracen in tracenames:
#         conf = confn.split("/")[-1].split("_")[0]
#         trace = tracen.split("/")[-1].split("-")[0]
#         print(conf)
#         print(trace)
#         if conf == "baseline":
#             baseline_dict[trace] = get_energy_conf_workload(confn, tracen, 4096, 512 * 4096, baseline_DRAM[trace] * 8)
#         if conf in conf2trace and conf2trace[conf] == trace:
#             optimized_dict[trace] = get_energy_conf_workload(confn, tracen, 4096, conf2block[conf] * 4096, optimized_DRAM[trace] * 8)



import sys

if __name__ == "__main__":
    import os
    import time
    from evaluate_target_conf import generate_config_workload, save_to_xdb, get_performance_from_xml

    confdir = "/home/daixuan2/learnedssd/aissd/xdb/nvme_mlc/configurations"
    tracedir = "/home/daixuan2/learnedssd/aissd/val_traces"
    traces = []
    # traces += [f"YCSB-0-0-{i}" for i in range(1, 4)]
    # traces += [f"TPCC-{i}-0-0" for i in range(1, 4)]
    # traces += [f"MapReduce-{i}-0-0" for i in range(1, 3)]
    # traces += [f"AdspayLoad-0-0-{i}" for i in range(1, 4)]
    # traces += [f"CloudStorage-{i}-0-0" for i in range(1, 10)]
    # traces += [f"WebSearch-{i}-0-0" for i in range(1, 3)]
    # traces += [f"LiveMapsBackEnd-1-0-{i}" for i in range(1, 10)]
    traces += [f"DevTool-{i}-0-{j}" for i in range(1, 2) for j in range(6, 7)]
    traces += [f"MSN-0-0-3", f"MSN-1-0-0"]
    traces += [f"VDI-2-0-0"]
    traces += [f"TPCCTest-1-0-0"]
    traces += [f"YCSBTest-0-0-1"]
    traces += [f"CloudStorageTest-1-0-0", f"CloudStorageTest-2-0-0"]
    confs = ["CS_same_op_same_CMT.xml", "DB_same_gc_same_CMT_same_op.xml"]

    confnames = [(confdir + "/" + fname) for fname in confs]
    tracenames = [(tracedir + "/" + fname) for fname in traces]
    for confname in confnames:
        for tracename in tracenames:
            evaluate_config_workload(confname, tracename)
    # print(sys.argv)
    # print(len(sys.argv))
    # if len(sys.argv) != 3:
    #     print("Usage : python3 evaluate_target_conf.py [path_to_configuration_file] [path_to_trace_file]")
    # conf_name = str(sys.argv[1])
    # trace_name = str(sys.argv[2])
    # evaluate_config_workload(conf_name, trace_name)

