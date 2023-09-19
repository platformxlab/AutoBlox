import json 
import numpy as np


f = open("coarsed_pruning.dat","r")
all_dict = json.loads(f.read())
f.close()

labelmapping = {"CS":"CloudStorage",
                "MR":"BatchDataAnalytics",
                "DB":"DataBase",
                "KV":"KVStore",
                "LM":"LiveMaps",
                "RC":"Recommendations",
                "WS":"WebSearch"}

workloads = [ "CS","RC", "LM", "KV","DB","MR","WS"]

import matplotlib as PlotLib
import sys
import math
import matplotlib.pyplot as PyPlot
from matplotlib.backends.backend_pdf import PdfPages

# colors = ['limegreen', '#ff796c', 'royalblue', '#6495ED', '#96f97b', '#ffa07a' ,'#fac205', '#95d0fc',]
# hatches = ['', '\\\\\\', '////', '\\\\', '', '|||', '---', '+++', 'xxx', 'ooo', '\\\\\\', 'ooo', '***']
mkrs = ['o','v','^','<','>']
fmts = ["r","g","b","c","m","y","k"]
key2mkrs = {}
key2fmts = {}
count = 0
for key in all_dict:
    datadict = all_dict[key]
    for key1 in datadict:
        if key1 in key2mkrs:
            continue
        key2mkrs[key1] = mkrs[count%(len(mkrs))]
        key2fmts[key1] = fmts[count%(len(fmts))]
        count += 1
PlotLib.rcParams["font.family"] = 'Arial'
PlotLib.use('Agg')

PlotLib.rcParams['hatch.linewidth'] = 0.5
colors = ['#ff796c', '#fac205', '#95d0fc', '#96f97b']

hatches = ['', '\\\\\\', '////', '\\\\', '', '|||', '---', '+++', 'xxx', 'ooo', '\\\\\\', 'ooo', '***']


figname = "coarsed_pruning.pdf"
Figure = PyPlot.figure(figsize=(12,2.4))
PlotLib.rcParams.update({'font.family': 'serif'})
PDF = PdfPages(figname)
figcount = 1
xticks = []

i = 0
labeled = []
for key in workloads:
    if key not in all_dict:
        continue
    cat = key
    # data to plot
    plt = PyPlot.subplot(int("17" + str(figcount)))
    plt.set_title(labelmapping[key], fontsize=8)
    figcount += 1
    i = i + 1
    x = [0, 1, 2, 3, 4]
    count = 0
    datadict = all_dict[key]
    for key1 in datadict:
        # Whether it is in the critical session
        # if datadict[key1][4] - datadict[key1][0] < 1e-2:
        #     continue
        for i in range(len(datadict[key1])):
            datadict[key1][i] = datadict[key1][i] * 2
        if key1 not in labeled and key=="CS":
            labeled.append(key1)
            plt.plot(x, datadict[key1],key2mkrs[key1]+"-"+key2fmts[key1], label=key1)
        else:
            if key1 not in labeled:
                labeled.append(key1)
                plt.plot(x, datadict[key1],key2mkrs[key1]+"-"+key2fmts[key1], label=key1)
            else:
                plt.plot(x, datadict[key1],key2mkrs[key1]+"-"+key2fmts[key1])
        count += 1
    # plt.set_title(key, fontsize=8)
    if key == "CS" or len(all_dict.keys()) == 1:
        handles, labels = plt.get_legend_handles_labels()
        lg=plt.legend(prop={'size':8}, ncol=4,  borderaxespad=0., edgecolor='black', bbox_to_anchor=(8.9, 2.0))
    # lg.draw_frame(False)
#     plt.xlabel('increase of parameter', fontsize=14)
#     plt.ylabel('Relative Latency Improvement', fontsize=14) 1
    plt.set_xticks([0,1,2,3,4])
    plt.set_xticklabels(["1x","2x","4x","8x","16x"] , fontsize=8, rotation = 0)
    plt.set_axisbelow(True)
    plt.yaxis.grid(color='lightgray', linestyle='solid')
    if key=="CS" or len(all_dict.keys()) == 1:
        plt.set_ylabel('Normalized Performance Improvement',fontsize=8)
    plt.set_ylim((-3, 3.5))
    
    #lg.draw_frame(False)
    
Figure.subplots_adjust(wspace=0.38, hspace=0.3)

PDF.savefig(Figure, bbox_inches='tight')
PDF.close()  
