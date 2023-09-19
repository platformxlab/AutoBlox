# get coarsed pruning
import time
from evaluate_target_conf import generate_config_workload, save_to_xdb, get_performance_from_xml, generate_queuetest_config_workload
from evaluate_target_conf import evaluate_config_workload_nonstop as evaluate_config_workload
import json

if __name__ == "__main__":
    import sys
    import os

    print ('Number of arguments:', len(sys.argv), 'arguments.')
    print ('Argument List:', str(sys.argv))

    if len(sys.argv) != 2:
        print("Usage: get_coarsed_pruning_data.py target_name")
        exit()

    target_workload = sys.argv[1]
    trace_dir = "../test_traces"
    all_traces = []
    for trace in os.listdir(trace_dir):
        if trace.startswith(target_workload + "-") and not trace.endswith("-0-0-0"):
            all_traces.append(trace)
    
    parameter_perf = {}

    # coarsed layout
    f = open("../xdb/coarsed_pruning_layout/" + "confid2name.dat", "r")
    confid2name = json.loads(f.read())
    f.close()

    f = open("../xdb/coarsed_pruning_layout/" + "confs.dat", "r")
    confs = json.loads(f.read())
    f.close()
    configuration_directory = "../xdb/coarsed_pruning_layout/configurations/"
    normalized_performances = [1]

    for i in range(1, len(confs)):
        configuration_perf = [1, 1]
        count = 0
        for trace in all_traces:
            result_base = evaluate_config_workload(configuration_directory  + str(0) + ".xml", trace_dir + "/" + trace)
            result = evaluate_config_workload(configuration_directory  + str(i) + ".xml", trace_dir + "/" + trace)
            if not result or not result_base:
                continue
            configuration_perf[0] *= result_base[0] / result[0]
            configuration_perf[1] *= result[4] / result_base[4]
            count += 1
        if count != 0:
            configuration_perf[0] = configuration_perf[0] ** (1 / count)
            configuration_perf[1] = configuration_perf[1] ** (1 / count)
            normalized_performances.append((configuration_perf[1] * configuration_perf[0]) ** (1 / 2))
        else:
            normalized_performances.append(-1)
    
    for i in range(1, len(confs)):
        id_diff = 0
        for j in range(len(confs[0])):
            if confs[i][j] != confs[0][j]:
                id_diff = j
                break
        name = confid2name[int(id_diff)]
        print(name)
        print(id_diff)
        if name not in parameter_perf:
            parameter_perf[name] = {confs[0][id_diff] : 1}
        parameter_perf[name][int(confs[i][id_diff])] = normalized_performances[i]
    # print("After layout:")
    # print(parameter_perf)
    # input()
    # coarsed non layout
    # TODO change this path
    f = open("../xdb/coarsed_pruning/" + "confid2name.dat", "r")
    confid2name = json.loads(f.read())
    f.close()

    f = open("../xdb/coarsed_pruning/" + "confs.dat", "r")
    confs = json.loads(f.read())
    f.close()
    configuration_directory = "../xdb/coarsed_pruning/configurations/"
    normalized_performances = [1]

    for i in range(1, len(confs)):
        configuration_perf = [1, 1]
        count = 0
        for trace in all_traces:
            result_base = evaluate_config_workload(configuration_directory  + str(0) + ".xml", trace_dir + "/" + trace)
            result = evaluate_config_workload(configuration_directory + str(i) + ".xml", trace_dir + "/" + trace)
            print(result_base)
            print(result)
            if not result or not result_base:
                continue
            configuration_perf[0] *= result_base[0] / result[0]
            configuration_perf[1] *= result[4] / result_base[4]
            count += 1
        # print(configuration_perf)
        # print()
        # input()
        if count != 0:
            configuration_perf[0] = configuration_perf[0] ** (1 / count)
            configuration_perf[1] = configuration_perf[1] ** (1 / count)
            normalized_performances.append((configuration_perf[1] * configuration_perf[0]) ** (1 / 2))
        else:
            normalized_performances.append(-1)
    
    for i in range(1, len(confs)):
        id_diff = 0
        for j in range(len(confs[0])):
            if confs[i][j] != confs[0][j]:
                id_diff = j
                break
        name = confid2name[int(id_diff)]
        if name not in parameter_perf:
            parameter_perf[name] = {confs[0][id_diff] : 1}
        parameter_perf[name][int(confs[i][id_diff])] = normalized_performances[i]
    # input()
    # print(parameter_perf)
    # print(normalized_performances)
    # input()
    import math
    delete_names = []
    for name in parameter_perf:
        print(name)
        print(parameter_perf[name])
        # input()
        if len(parameter_perf[name].keys()) == 5:
            if parameter_perf[name][0] == -1:
                parameter_perf[name][0] = parameter_perf[name][1]
            if parameter_perf[name][4] == -1:
                if parameter_perf[name][3] == -1:
                    parameter_perf[name][3] = parameter_perf[name][2]
                parameter_perf[name][4] = parameter_perf[name][3]
            if parameter_perf[name][1] == -1:
                parameter_perf[name][1] = (parameter_perf[name][0] + parameter_perf[name][2]) / 2
            if parameter_perf[name][2] == -1:
                parameter_perf[name][2] = (parameter_perf[name][1] + parameter_perf[name][3]) / 2
            if parameter_perf[name][3] == -1:
                parameter_perf[name][3] = (parameter_perf[name][2] + parameter_perf[name][4]) / 2
            parameter_perf[name] = [math.log(parameter_perf[name][0] / parameter_perf[name][0]), math.log(parameter_perf[name][1] / parameter_perf[name][0]),math.log(parameter_perf[name][2] / parameter_perf[name][0]),math.log(parameter_perf[name][3] / parameter_perf[name][0]),math.log(parameter_perf[name][4] / parameter_perf[name][0])] 
        else:
            delete_names.append(name)
    delete_names.append("IO_Queue_Depth")
    delete_names.append("Queue_Fetch_Size")
    for n in delete_names:
        del parameter_perf[n]
    print(len(parameter_perf.keys()))
    labelmapping = {"CloudStorage":"CS",
                "MapReduce":"MR",
                "TPCC":"DB",
                "YCSB":"KV",
                "LiveMapsBackEnd":"LM",
                "AdspayLoad":"RC",
                "WebSearch":"WS"}
    
    f = open("../reproduced_dat/coarsed_pruning.dat", "r")
    current_dat = json.loads(f.read())
    f.close()

    current_dat[labelmapping[target_workload]] = parameter_perf
    f = open("../reproduced_dat/coarsed_pruning.dat", "w+")
    f.write(json.dumps(current_dat))
    f.close()
    