# clustering version 2
# coinsidering all the explainable effects
# this file will produce k-means data in log/ directory

from numpy import linalg as LA
import math
import numpy as np
import os
import json
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
import numpy as np
import math
import matplotlib.pyplot as plt
import seaborn as sns

def load_trace(tracedir):
    print("load:" + tracedir)
    f = open(tracedir, "r")
    traces = f.readlines()
    f.close()
    for i in range(0, len(traces)):
        traces[i] = traces[i].split(" ")
        for j in range(0, len(traces[i])):
            traces[i][j] = float(traces[i][j])
    return traces

# max_tracelen = 1000000
window_size = 3000


exec_traces = sorted(os.listdir("../traces"), key=lambda x:x.split("-")[0] + x.split("-")[1].zfill(2))
training_dat = {}

excluded_cats = ["PageRank", "DevTool", "FINANCIAL", "FIUHome", "MailServer", "MLPrep", "MSN", "MSRHM", "MSRMDS", "MSRPRN", "MSRPROJ", "RadiusAuth",
                 "TPCCTest", "MSRPROXY", "TPCETest", "VDI", "YCSBTest", "YCSBBlockFlex",  "CloudStorage", "AdsDataServer"]

total_trace_entries_count = {}

for tracename in exec_traces:
    cat = tracename.split("-")[0]
    ids = tracename.split("-")
    if cat in excluded_cats:
        continue
    if cat not in training_dat:
        training_dat[cat] = []
    current_count = 0
    for item in training_dat[cat]:
        current_count += len(item)
    # if current_count >= max_tracelen:
    #     continue
    print("extracting:" + tracename)
    trace = load_trace("../traces/" + tracename)
    print("length =" + str(len(trace)))
    training_dat[cat].append(trace)
    total_trace_entries_count[cat] = current_count + len(trace)
    # print("Current Length of Category:" + str(current_count + len(trace)))
    # needed_tracelen = int((max_tracelen - current_count + window_size - 1) / window_size) * window_size
    # training_dat[cat].append(trace[0:min(len(trace), needed_tracelen)])


# extract 70% workload as training set for clustering
# also ensure that the variance is balanced acorss multiple traces by using same amount of trace entry for each category

min_entry = total_trace_entries_count[list(total_trace_entries_count.keys())[0]]
min_key = list(total_trace_entries_count.keys())[0]
for k in total_trace_entries_count.keys():
    if total_trace_entries_count[k] < min_entry:
        min_entry = total_trace_entries_count[k]
        min_key = k

if min_entry < 1000000:
    print("Not enough trace entries to cluster for " + str(min_key))

clustering_entries = int(min_entry * 0.6)


# split training and testing dataset

training = {}
testing_dat = {}

for k in total_trace_entries_count.keys():
    training[k] = []
    testing_dat[k] = []
    count = 0
    training_flag = True
    for trace in training_dat[k]:
        if not training_flag:
            testing_dat[k].append(trace)
        elif count + len(trace) > clustering_entries:
            training_flag = False
            training[k].append(trace[0:clustering_entries - count])
            testing_dat[k].append(trace[clustering_entries - count:len(trace)])
        else:
            training[k].append(trace)

training_dat = training.copy()

time_scale = 10**9
size_scale = 2**37
ioSize_scale = 256
ssd_num_scale = 33.0
# 0: timestamp,  1: DiskNum, 2: ByteOffset, 3: IOSize, 4: R/W
# here we say that the maximum number get the clustering result
trace2cat = {}
cat2trace = {}

trace2catarray = {}
# divide raw data into windows and among ssds
# remove the ssd num parameter after categorization
kmeans_data = []
begin = 0
end = 0

for cat in training_dat:
    if cat in excluded_cats:
        continue
    print("Converting: " + cat)
    traces = training_dat[cat]
    # first divide the trace among different SSDs
    traceid = -1
    for trace in traces:
        ssd2trace = {}
        traceid += 1
        print("Converting Trace Part:" + str(traceid))
        t0 = trace[0][0]
        max_ssd = 0.0
        for io in trace:
            if io[1] > max_ssd:
                max_ssd = io[1]
        for io in trace:
            if io[1] in ssd2trace:
                ssd2trace[io[1]].append([(io[0] - t0) / time_scale, io[2] / size_scale, io[3] / 256  , io[4], max_ssd / ssd_num_scale])
            else:
                ssd2trace[io[1]] = [[(io[0] - t0) / time_scale, io[2] / size_scale, io[3] / 256  , io[4], max_ssd / ssd_num_scale]]
        for ssd in ssd2trace:
            cur = 0
            print(len(ssd2trace[ssd]))
            if len(ssd2trace[ssd]) < 7 * window_size and cat == "MapReduce":
                continue
            while cur + window_size < len(ssd2trace[ssd]):
                kmeans_data.append(ssd2trace[ssd][cur:cur + window_size])
                for j in range(1, window_size):
                    kmeans_data[-1][j][0] -= (kmeans_data[-1][0][0] - 10**(-9))
                kmeans_data[-1][0][0] = 10**(-9)
                minaddr = 0
                for j in range(0, window_size):
                    if minaddr > kmeans_data[-1][j][1]:
                        minaddr = kmeans_data[-1][j][1]
                for j in range(0, window_size):
                    kmeans_data[-1][j][1] -= minaddr
#                 mean /= window_size
                for j in range(0, window_size):
                     kmeans_data[-1][j][1] = math.log(kmeans_data[-1][j][1] + 1e-9) / 2
                for j in range(0, window_size):
                    kmeans_data[-1][j][0] = (math.log(kmeans_data[-1][j][0]) + 10) / 20
                    kmeans_data[-1][j][2] = math.log(kmeans_data[-1][j][2]) / 10
                cur += window_size
    end = len(kmeans_data)
    trace2catarray[cat] = [begin, end]
    begin = end

print("generating KMeans")
for i in range(0, len(kmeans_data)):
    vec = np.array(kmeans_data[i])
    vec = np.transpose(vec)
    cur = [] # 0: timestamp; 1: i/o address; 2: i/o Size; 3: R/W
    for j in range(0, len(vec)):
        cur += vec[j].tolist()
    kmeans_data[i] = cur



f = open("../log/kmeans_data", "w")
f.write(json.dumps(kmeans_data))

f = open("../log/cat2kmeanspoints", "w")
f.write(json.dumps(trace2catarray))

f = open("../log/kmeans_data", "r")
kmeans_data = json.loads(f.read())
f.close()


f = open("../log/cat2kmeanspoints", "r")
trace2catarray = json.loads(f.read())
f.close()


catecount = 6

X = np.array(kmeans_data)
pca = PCA(n_components=2)
X_new = pca.fit_transform(X)
clustering = KMeans(n_clusters=catecount,random_state=0).fit(X_new)

f = open("../log/X_new.dat", "w")
f.write(json.dumps(X_new.tolist()))

trace2cat = {}
cat2trace = {}

for name in trace2catarray:
    judge = np.zeros(catecount)
    for i in range(trace2catarray[name][0], trace2catarray[name][1]):
        judge[clustering.labels_[i]] += 1
    print(name)
    print(judge)
    maxc = np.argmax(judge)
    maxc = maxc.tolist()
    maxv = judge[maxc]
    judge[maxc] = 0
    maxc2 = np.argmax(judge).tolist()
    maxv2 = judge[maxc]
    if maxv < maxv2 * 2:
        trace2cat[name] = [maxc, maxc2]
        if maxc not in cat2trace:
            cat2trace[maxc] = []
        if maxc2 not in cat2trace:
            cat2trace[maxc] = []
        cat2trace[maxc].append(name)
        cat2trace[maxc2].append(name)
    else:
        trace2cat[name] = [maxc]
        if maxc not in cat2trace:
            cat2trace[maxc] = []
        cat2trace[maxc].append(name)


colors = ["blue","aqua","black","red","darkorange","yellow","green","magenta","indigo"]
colored = []

catcolor = {'AdsDataServer': 0,
 'AdspayLoad': 1,
 'LiveMapsBackEnd': 2,
 'YCSB': 3,
 'CloudStorage': 4,
 'MapReduce': 5,
 'TPCC': 6,
 'TPCE': 7,
 "WebSearch" : 8,
 'PageRank' : 0
}


# for name in trace2catarray:
#     cat = name.split("-")[0]
#     for i in range(trace2catarray[name][0], trace2catarray[name][1]):
#         plt.scatter(X_new[i,0], X_new[i,1],color=colors[catcolor[cat]],marker='o')


# plt.savefig("./debuglog/groundtruth.jpg")

# for i in range(0, len(X_new)):
#     plt.scatter(X_new[i,0], X_new[i,1],color=colors[clustering.labels_[i]],marker='o')


# plt.legend( loc = 'upper left')
# plt.savefig("./debuglog/kmeans.jpg")

# f = open("../log/cat2trace", "w+")
# f.write(json.dumps(cat2trace))
# f.close()

# f = open("../log/trace2cat", "w+")
# f.write(json.dumps(trace2cat))
# f.close()

components = pca.components_.tolist()
sorted_x = sorted(components[0])
sorted_xid = [components[0].index(x) for x in sorted_x]
sorted_y = sorted(components[1])
sorted_yid = [components[1].index(y) for y in sorted_y]

# for i in list(range(158, 202)) + list(range(42,84)):
#     print(kmeans_data[i][8000])




# for cat in training_dat:
#     if cat in evaluate_cats:
#         continue
#     print("Converting: " + cat)
#     traces = training_dat[cat]
#     # first divide the trace among different SSDs
#     traceid = -1
#     for trace in traces:
#         ssd2trace = {}
#         traceid += 1
#         print("Converting Trace Part:" + str(traceid))
#         t0 = trace[0][0]
#         max_ssd = 0.0
#         for io in trace:
#             if io[1] > max_ssd:
#                 max_ssd = io[1]
#         for io in trace:
#             if io[1] in ssd2trace:
#                 ssd2trace[io[1]].append([(io[0] - t0) / time_scale, io[2] / size_scale, io[3] / 256  , io[4]])
#             else:
#                 ssd2trace[io[1]] = [[(io[0] - t0) / time_scale, io[2] / size_scale, io[3] / 256  , io[4]]]
#         for ssd in ssd2trace:
#             cur = 0
#             while cur + window_size < len(ssd2trace[ssd]):
#                 kmeans_data.append(ssd2trace[ssd][cur:cur + window_size])
#                 for j in range(1, window_size):
#                     kmeans_data[-1][j][0] -= (kmeans_data[-1][0][0] - 10**(-9))
#                 kmeans_data[-1][0][0] = 10**(-9)
#                 minaddr = 0
#                 for j in range(0, window_size):
#                     if minaddr > kmeans_data[-1][j][1]:
#                         minaddr = kmeans_data[-1][j][1]
#                 for j in range(0, window_size):
#                     kmeans_data[-1][j][1] -= minaddr
# #                 mean /= window_size
#                 for j in range(0, window_size):
#                      kmeans_data[-1][j][1] = math.log(kmeans_data[-1][j][1] + 1e-9) /2
#                 for j in range(0, window_size):
#                     kmeans_data[-1][j][0] = (math.log(kmeans_data[-1][j][0]) + 10) / 20
#                     kmeans_data[-1][j][2] = math.log(kmeans_data[-1][j][2]) / 10
#                 cur += window_size
#     end = len(kmeans_data)
#     trace2catarray[cat] = [begin, end]
#     begin = end
