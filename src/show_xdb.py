import os 
xdb_path = "../xdb/"

# get tables
# tables = os.listdir(xdb_path)
# print("select from the following to display target table")

target_table = "nvme_mlc_wtif"
if target_table not in os.listdir(xdb_path):
    print("ERROR: TARGET TABLE NOT EXIST!")
    exit(0)


# Read the relevant performance and file discriptors
import json
crTableFilefp = open(xdb_path + target_table + "/crTable.json", "r")
crTable = json.loads(crTableFilefp.read())
crTableFilefp.close()


# Wipe out all the redundant data and write back
del_list = []
for confname in crTable:
    for workloadname in crTable[confname]:
        crTable[confname][workloadname] = [crTable[confname][workloadname][-1]]
    if workloadname.endswith("-0-0-0"):
        del_list.append(workloadname)


for key1, key2 in del_list:
    del crTable[key1][key2]


crTableFilefp = open(xdb_path + target_table + "/crTable.json", "w")
crTableFilefp.write(json.dumps(crTable))
crTableFilefp.close()


# Calculate improvement for each configuration
if "baseline" not in crTable:
    print("ERROR! baseline configurations not in crTable!")
# Result Table: 
# *** First Index: Configuraton Name
# *** Second Index: Category Name
# *** Third Index: 
# (1) An "avg_bw_impv" with geometry average bandwidth improvement
# (2) An "avg_latency_impv" with geometry average of latency improvement
# (3) "TraceName" - [avg_bw_improvement, avg_throughput_improvement] pairs


result_table = {}
for confname in crTable:
    if confname == "baseline":
        continue
    result_table[confname] = {}
    for tracename in crTable[confname]:
        if tracename not in crTable["baseline"]:
            print("WARNING: BASELINE NOT PERFORMING TRACE " + tracename)
            continue
        category = tracename.split("-")[0]
        if category not in result_table[confname]:
            result_table[confname][category] = {}
        result_table[confname][category][tracename] = [crTable["baseline"][tracename][0][0] / crTable[confname][tracename][0][0],
                                                        crTable[confname][tracename][0][4] / crTable["baseline"][tracename][0][4]]
    for category in result_table[confname]:
        avg_bw_impv = 1
        avg_latency_impv = 1
        count = 0
        for tracename in result_table[confname][category]:
            count += 1
            avg_bw_impv *= result_table[confname][category][tracename][1]
            avg_latency_impv *= result_table[confname][category][tracename][0]
        avg_bw_impv = avg_bw_impv ** (1.0 / count)
        avg_latency_impv = avg_latency_impv ** (1.0 / count)
        result_table[confname][category]["avg_bw_impv"] = avg_bw_impv
        result_table[confname][category]["avg_latency_impv"] = avg_latency_impv


resultTableFilefp = open(xdb_path + target_table + "/result_table.json", "w")
resultTableFilefp.write(json.dumps(result_table))
resultTableFilefp.close()

# for unseen workload test
# stoplist=["YCSB", "TPCC", "MapReduce", "AdspayLoad", "CloudStorage", "WebSearch", "LiveMapsBackEnd",
#         "PageRank", "DevTool", "MSN", "MLPrep", "PageRank"]
# for ordinary test
# stoplist=["YCSBTest", "TPCCTest", "CloudStorageTest", "VDI", "FIUHome", "RadiusAuth",
#         "PageRank", "DevTool", "MSN", "MLPrep", "PageRank"]

# for balance coefficient test
stoplist=["YCSBTest", "TPCCTest", "CloudStorageTest", "VDI", "FIUHome", "RadiusAuth",
        "PageRank", "DevTool", "MSN", "MLPrep", "PageRank"]


# for latency and throughput balance
alpha = 0.9
# for target and non-target balance
beta = 0.5

# get configuration file for 
def get_c_score(confname, target_category):
    if category in stoplist or category not in result_table[confname]:
        print(f"ERROR processing {confname}, confname not in result_table.")
        return -1
    avg_lat = result_table[confname][category]["avg_latency_impv"]
    avg_bw = result_table[confname][category]["avg_bw_impv"]
    print(f"***** {category} : {avg_lat}/{avg_bw}")
    # calculate the geo mean of other workloads
    avg_non_target_lat = 1.0
    avg_non_target_bw = 1.0
    count = 0
    for other_cate in result_table[confname]:
        if other_cate == category:
            continue
        if other_cate in stoplist:
            continue
        avg_non_target_bw *= result_table[confname][other_cate]["avg_bw_impv"]
        avg_non_target_lat *= result_table[confname][other_cate]["avg_latency_impv"]
        count += 1
    if count == 0:
        return -1
    avg_non_target_bw = avg_non_target_bw ** (1 / count)
    avg_non_target_lat = avg_non_target_lat ** (1 / count)
    return beta * (alpha * avg_lat + (1 - alpha) * avg_bw) + (1 - beta) * (alpha * avg_non_target_lat + (1 - alpha) * avg_non_target_bw)


def display_configname(confname, target_category=None):
    print(f"\n       ******* Testify Configuration *******: {confname}\n")
    for category in result_table[confname]:
        if category in stoplist:
            continue
        avg_lat = result_table[confname][category]["avg_latency_impv"]
        avg_bw = result_table[confname][category]["avg_bw_impv"]
        print(f"***** {category} : {avg_lat}/{avg_bw}")
        # calculate the geo mean of other workloads
        avg_non_target_lat = 1
        avg_non_target_bw = 1
        count = 0
        for other_cate in result_table[confname]:
            if other_cate == category:
                continue
            if other_cate in stoplist:
                continue
            avg_non_target_bw *= result_table[confname][other_cate]["avg_bw_impv"]
            avg_non_target_lat *= result_table[confname][other_cate]["avg_latency_impv"]
            count += 1
        if count == 0:
            continue
        avg_non_target_bw = avg_non_target_bw ** (1 / count)
        avg_non_target_lat = avg_non_target_lat ** (1 / count)
        if target_category == None or target_category == category: 
            print(f"*** Non-Target : {avg_non_target_lat}/{avg_non_target_bw}")
    # print(f"***** Detail Configuration Performance *****\n")
    # for category in result_table[confname]:
    #     print(f"*** {category} ***: \n")
    #     for tracename in result_table[confname][category]:
    #         if tracename != "avg_latency_impv" and tracename != "avg_bw_impv":
    #             avg_lat = result_table[confname][category][tracename][0]
    #             avg_bw = result_table[confname][category][tracename][1]
    #             print(f"{tracename} : {avg_lat}/{avg_bw}\n")

# store five top configurations for this 
categories = {}

# get all categories
for confname in result_table:
    for category in result_table[confname]:
        if category not in categories:
            categories[category] = []

print(categories)

for confname in result_table:
    for category in result_table[confname]:
        i = 0
        thisscore = get_c_score(confname, category)
        for cname, score in categories[category]:
            if score < thisscore:
                break
            else:
                i += 1
        categories[category].insert(i, [confname, thisscore])


for category in ["YCSB"]:
# for category in categories:
# for category in ["LiveMapsBackEnd"]:
    if category in stoplist:
        continue
    print(f"\n\n******** Best Configurations for Category {category}, with Coefficient Alpha={alpha}, Beta={beta} ")
    categories[category] = categories[category]
    for cname, score in categories[category]:
        print(cname)
        if cname.startswith("baseline"):
            continue
        display_configname(cname, category)

# previous display
# for category in ["YCSB", "AdspayLoad"]:
# for category in categories:
#     if category in stoplist:
#         continue
#     print(f"\n\n******** Best Configurations for Category, with Coefficient Alpha={alpha}, Beta={beta} " + category)
#     categories[category] = categories[category][0:10]
#     for cname, avg_lat1, avg_bw1 in categories[category]:
#         if cname.startswith("baseline"):
#             continue
#         display_configname(cname, category)