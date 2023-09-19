# this file is for inspection of how each configuration evolveduring the Training Process
import find_best_conf
from find_best_conf import update_xdb, geo_mean
from find_best_conf import tunable_configuration_names, explored_configurations, xdbTable, baseline_conf, target_workload



# show how is the performance and configuration different from the baseline configuration
def show_configuration_detail(confid, workload_cat, explored_configurations, xdbTable, max_grade, max_id, conv_count, equal_grades):
    print(f"Probing detail of configuration {confid} for target workload {workload_cat}")
    if int(confid) == 0:
        print("This is baseline configuration.")
        return None, None, max_grade, max_id, conv_count, equal_grades
    if str(confid) not in xdbTable:
        print("This config does not exist")
        return None, None, max_grade, max_id, conv_count, equal_grades
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
    for item in changed_parameters_and_value:
        print(f"{item[0]} : {item[1]} -> {item[2]}")
    return results, changed_parameters_and_value, max_grade, max_id, conv_count, equal_grades



xdbTable, explored_configurations = update_xdb(xdbTable, explored_configurations, [baseline_conf], {}, target_workload, True, True)
max_grade = 0
max_id = 0
conv_count = 0
equal_grades = []

for i in range(len(explored_configurations)):
    a, b, max_grade, max_id, conv_count, equal_grades = show_configuration_detail(i, target_workload, explored_configurations, xdbTable, max_grade, max_id, conv_count, equal_grades)
    input()