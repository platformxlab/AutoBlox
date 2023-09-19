import json 
import numpy as np
import matplotlib as PlotLib
import sys
import math
import matplotlib.pyplot as PyPlot
from matplotlib.backends.backend_pdf import PdfPages

labelmapping = { "RC":"Recommendations",
                "KV":"KVStore",
                "DB":"DataBase",
                "WS":"WebSearch",
                "MR":"MapReduce",
                "CS":"CloudStorage",
                "LM":"LiveMaps"}

f = open("./tuning_time.dat","r")
data = json.loads(f.read())
f.close()
tuning_time = data[0]
tuning_time_noorder = data[1]

# colors = ['limegreen', '#ff796c', 'royalblue', '#6495ED', '#96f97b', '#ffa07a' ,'#fac205', '#95d0fc',]
# hatches = ['', '\\\\\\', '////', '\\\\', '', '|||', '---', '+++', 'xxx', 'ooo', '\\\\\\', 'ooo', '***']
mkrs = ['.','^','x','v','^','o','v','<','>']
# mkrs = [" "]
fmts = ["r","c","g","b","c","m","y","k"]
key2mkrs = {}
key2fmts = {}
count = 0
for key1 in tuning_time:
    if key1 in key2mkrs:
        continue
    key2mkrs[key1] = [mkrs[count%(len(mkrs))], mkrs[(count + 1)%(len(mkrs))]]
    key2fmts[key1] = [fmts[count%(len(fmts))], fmts[(count + 1)%(len(fmts))]]
PlotLib.rcParams["font.family"] = 'Arial'
PlotLib.use('Agg')

PlotLib.rcParams['hatch.linewidth'] = 0.5
colors = ['#ff796c', '#fac205', '#95d0fc', '#96f97b']

hatches = ['', '\\\\\\', '////', '\\\\', '', '|||', '---', '+++', 'xxx', 'ooo', '\\\\\\', 'ooo', '***']


figname = "tuning_time.pdf"
Figure = PyPlot.figure(figsize=(12, 1.7))
PlotLib.rcParams.update({'font.family': 'serif'})
PDF = PdfPages(figname)
figcount = 1
xticks = []

i = 0
labeled = []
for key in labelmapping:
    if key not in tuning_time:
        continue
    cat = key
    # data to plot
    plt = PyPlot.subplot(int("17" + str(figcount)))
    plt.set_title(key, fontsize=5)
    figcount += 1
    i = i + 1
    # time
    x1 = [0]
    y1 = [1.0]
    for item in tuning_time[cat]:
        x1.append(item[0] / 3600 + 0.1)
        y1.append(np.exp(item[1]).tolist())
    x1.append(10.0)
    y1.append(y1[-1])
    x2 = [0]
    y2 = [1.0]
    for item in tuning_time_noorder[cat]:
        if item[0] / 3600 > 9:
            continue
        x2.append(item[0] / 3600 + 0.1)
        y2.append(np.exp(item[1]).tolist())
    x2.append(10.0)
    y2.append(y2[-1])
    if key == "RC" or len(tuning_time.keys()) == 1:
        plt.plot(x1, y1, key2mkrs[key][0]+"-"+key2fmts[key][0], label="Without learning order enforced")
        plt.plot(x2, y2, key2mkrs[key][1]+"-"+key2fmts[key][1], label="With learning order enforced")
        handles, labels = plt.get_legend_handles_labels()
        lg=plt.legend(prop={'size':10}, ncol=4, borderaxespad=0., edgecolor='black', bbox_to_anchor=(7.3, 1.4))
#         lg=plt.legend(prop={'size':8}, ncol=4,  borderaxespad=0., edgecolor='black', bbox_to_anchor=(1.0, 2.0))
    else:
        plt.plot(x1, y1,key2mkrs[key][0]+"-"+key2fmts[key][0])
        plt.plot(x2, y2,key2mkrs[key][1]+"-"+key2fmts[key][1])
    plt.set_title(labelmapping[key], fontsize=8)
    plt.set_axisbelow(True)
    plt.set_xlim(0, 10)
    plt.set_ylim(0.9, 1.7)
    plt.yaxis.grid(color='lightgray', linestyle='solid')
    if key=="RC" or len(tuning_time.keys()) == 1:
        plt.set_ylabel('Normalized SSD \nPerformance Speedup',fontsize=8)
    plt.set_xlabel('Learning Time (hrs)',fontsize=8)
    plt.set_xticks(plt.get_xticks()[::1])
    
    
Figure.subplots_adjust(wspace=0.38, hspace=0.3)

PDF.savefig(Figure, bbox_inches='tight')
PDF.close()  
