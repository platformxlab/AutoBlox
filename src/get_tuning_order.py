# get coarsed pruning
import time
from evaluate_target_conf import generate_config_workload, save_to_xdb, get_performance_from_xml, generate_queuetest_config_workload
from evaluate_target_conf import evaluate_config_workload_nonstop as evaluate_config_workload
import json
from sklearn import linear_model

if __name__ == "__main__":
    import sys
    import os

    print ('Number of arguments:', len(sys.argv), 'arguments.')
    print ('Argument List:', str(sys.argv))

    if len(sys.argv) != 2:
        print("Usage: get_tuning_order.py target_name")
        exit()

    target_workload = sys.argv[1]
    trace_dir = "../test_traces"
    all_traces = []
    for trace in os.listdir(trace_dir):
        # use one trace from LiveMaps
        if trace == "LiveMapsBackEnd-1-0-8":
            continue
        if trace.startswith(target_workload + "-") and not trace.endswith("-0-0-0"):
            all_traces.append(trace)
    
    parameter_perf_non_layout = {}

    
    # coarsed non layout
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
            normalized_performances.append((configuration_perf[0] ** (0.9)) * (configuration_perf[1] ** (0.1)))
        else:
            normalized_performances.append(-1)
    parameter_perf = {}
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
            parameter_perf[name] = [math.log(parameter_perf[name][0] ), math.log(parameter_perf[name][1] ),math.log(parameter_perf[name][2] ),math.log(parameter_perf[name][3] ),math.log(parameter_perf[name][4])] 
        else:
            # calculate max - min for parameter_perf
            # print(name)
            # print(parameter_perf[name])
            # input()
            max_val = parameter_perf[name][0]
            min_val = parameter_perf[name][0]
            for val in parameter_perf[name]:
                if parameter_perf[name][val] == -1:
                    continue
                else:
                    if parameter_perf[name][val] > max_val:
                        max_val = parameter_perf[name][val]
                    if parameter_perf[name][val] < min_val or min_val == -1:
                        min_val = parameter_perf[name][val]
            parameter_perf[name] = [max_val - min_val]
    delete_names.append("IO_Queue_Depth")
    delete_names.append("Queue_Fetch_Size")
    delete_names.append("SATA_Processing_Delay")
    delete_names.append("Page_Metadat_Capacity")
    delete_names.append("Suspend_Erase_Time")
    delete_names.append("Suspend_Program_time")
    delete_names.append("Block_PR_Cycles_Limit")
    delete_names.append("Page_Program_Latency_CSB")
    delete_names.append("Page_Read_Latency_CSB")
    delete_names.append("Preferred_suspend_write_time_for_read")
    delete_names.append("Preferred_suspend_erase_time_for_write")
    delete_names.append("Preferred_suspend_erase_time_for_read")
    delete_names.append("Static_Wearleveling_Threshold")
    delete_names.append("ResponseTime_Logging_Period_Length")
    for n in delete_names:
        del parameter_perf[n]
    
    for name in parameter_perf:
        if len(parameter_perf[name]) == 1:
            parameter_perf[name] = parameter_perf[name][0]
            continue
        clf = linear_model.Ridge()
        X = [[0],[1],[2],[3],[4]]
        y = parameter_perf[name]
        clf.fit(X,y)
        parameter_perf[name] = clf.coef_[0].tolist()
    
    # fine_grained
    f = open("../xdb/fine_grained_pruning/" + "confid2name.dat", "r")
    confid2name = json.loads(f.read())
    f.close()

    f = open("../xdb/fine_grained_pruning/" + "confs.dat", "r")
    confs = json.loads(f.read())
    f.close()
    configuration_directory = "../xdb/fine_grained_pruning/configurations/"
    normalized_performances = [1]

    for i in range(1, len(confs)):
        configuration_perf = [1, 1]
        count = 0
        for trace in all_traces:
            result_base = evaluate_config_workload(configuration_directory  + str(132) + ".xml", trace_dir + "/" + trace)
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
            normalized_performances.append(math.log((configuration_perf[0] ** (0.9)) * (configuration_perf[1] ** (0.1))))
        else:
            normalized_performances.append(1)
    print(normalized_performances)
    # input()
    ids = []
    for i in range(0, len(confs)):
        for j in range(len(confs[i])):
            if confs[i][j] != confs[132][j]:
                if j not in ids:
                    ids.append(j)
    # encode confs
    encoded_confs = []
    for i in range(0, len(confs)):
        code = []
        for idx in ids:
            code.append(confs[i][idx])
        encoded_confs.append(code)
    print(encoded_confs)
    # input()
    clf = linear_model.Ridge()
    clf.fit(encoded_confs, normalized_performances)
    print(clf.coef_)
    # input()
    for i in range(len(ids)):
        parameter_perf[confid2name[int(ids[i])]] = clf.coef_[i].tolist()
    print(len(parameter_perf.keys()))
    
    # process the parameter_perf into tuning order
    sorted_parameters_coeffs = []

    # insertion sort
    for name in parameter_perf:
        val = parameter_perf[name]
        insert_place = -1
        for i in range(len(sorted_parameters_coeffs)):
            if sorted_parameters_coeffs[i][1] < abs(val):
                insert_place = i
                break
        if insert_place == -1:
            sorted_parameters_coeffs.append([name, abs(val)])
        else:
            sorted_parameters_coeffs.insert(insert_place, [name, abs(val)])
    print(parameter_perf)
    print(sorted_parameters_coeffs)
    # input()
    tuning_order = []
    layouts = ["Flash_Channel_Count", "Chip_No_Per_Channel", "Die_No_Per_Chip", "Plane_No_Per_Die", "Block_No_Per_Plane", "Page_No_Per_Block"]
    layout_added = False
    caches = ["Data_Cache_Capacity", "CMT_Capacity"]
    caches_added = False
    cur_val = -1
    skipped_parameters_for_this_exp = ["IO_Queue_Depth", "Queue_Fetch_Size", "Block_Erase_Latency", "Page_Program_Latency_MSB", "Page_Program_Latency_CSB","Page_Program_Latency_LSB", "Page_Read_Latency_MSB", "Page_Read_Latency_CSB", "Page_Read_Latency_LSB"]
    for i in range(len(sorted_parameters_coeffs)):
        item = sorted_parameters_coeffs[i]
        if item[0] in skipped_parameters_for_this_exp:
            continue
        if abs(item[1]) < 0.005:
            break
        current_selected_candidates = [item[0]]
        if item[0] in layouts and layout_added:
            continue
        elif item[0] in layouts:
            current_selected_candidates = layouts
            layout_added = True
        if item[0] in caches and caches_added:
            continue
        elif item[0] in caches:
            current_selected_candidates = caches
            caches_added = True
        print(current_selected_candidates)
        print(tuning_order)
        print(cur_val)
        print(item[1])
        print(item[0])
        # input()
        if cur_val != -1:
            if abs(item[1]) >= 0.5 * cur_val:
                current_selected += current_selected_candidates
                current_selected_candidates = []
                continue
            else:
                tuning_order.append(current_selected)
        current_selected = current_selected_candidates
        if item[0] in layouts:
            cur_val = abs(item[1])
            for layoutname in layouts:
                if abs(parameter_perf[layoutname]) < cur_val and abs(parameter_perf[layoutname]) >= 0.005:
                    cur_val = abs(parameter_perf[layoutname])
        elif item[0] in caches:
            cur_val = abs(item[1])
            for layoutname in caches:
                if abs(parameter_perf[layoutname]) < cur_val:
                    cur_val = abs(parameter_perf[layoutname])
        else:
            cur_val = abs(item[1])
        current_selected_candidates = []
    
    tuning_order.append(current_selected)
    
    f = open("../reproduced_dat/tuning_order.dat", "r")
    current_dat = json.loads(f.read())
    f.close()

    current_dat[target_workload] = tuning_order
    f = open("../reproduced_dat/tuning_order.dat", "w+")
    f.write(json.dumps(current_dat))
    f.close()
    

