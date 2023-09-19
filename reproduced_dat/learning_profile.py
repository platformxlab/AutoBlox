import numpy as np


import matplotlib as PlotLib
import sys
import math
import matplotlib.pyplot as PyPlot
from matplotlib.backends.backend_pdf import PdfPages
import json

f = open("learning_profile.dat", "r")
data = json.loads(f.read())
f.close()

tuning_order_names = data[0]
all_results = data[1]
all_time = data[2]

# colors = ['limegreen', '#ff796c', 'royalblue', '#6495ED', '#96f97b', '#ffa07a' ,'#fac205', '#95d0fc',]
# hatches = ['', '\\\\\\', '////', '\\\\', '', '|||', '---', '+++', 'xxx', 'ooo', '\\\\\\', 'ooo', '***']
mkrs = ['.','o','v','^','<','>']
fmts = ["r","g","b","c","m","y","k"]
key2mkrs = {}
key2fmts = {}
count = 0
for name in tuning_order_names:
    key1 = name
    key2mkrs[key1] = mkrs[count%(len(mkrs))]
    key2fmts[key1] = fmts[count%(len(fmts))]
    count += 1
PlotLib.rcParams["font.family"] = 'Arial'
PlotLib.use('Agg')

PlotLib.rcParams['hatch.linewidth'] = 0.5
colors = ['#ff796c', '#fac205', '#95d0fc', '#96f97b']

hatches = ['', '\\\\\\', '////', '\\\\', '', '|||', '---', '+++', 'xxx', 'ooo', '\\\\\\', 'ooo', '***']



figname = "learning_profile.pdf"
Figure = PyPlot.figure(figsize=(12,1.5))
PlotLib.rcParams.update({'font.family': 'serif'})
PDF = PdfPages(figname)
figcount = 1
xticks = []
figurenames = ["With learning order enforced", "Without learnig order enforced"]
labeled = []
for i in range(2):
    plt = PyPlot.subplot(1, 2, figcount)
    plt.set_title(figurenames[i], fontsize=9)
    conf_length = 1
    for j in range(0, len(tuning_order_names)):
        key1 = tuning_order_names[j]  
        data = all_results[i][1][key1]
#         x = np.arange(0, len(data), 1).tolist()
        conf_length = len(data)
        labeled.append(key1)
        data = data[0:len(all_time[i])]
        plt.plot(all_time[i], data,key2mkrs[key1]+"-"+key2fmts[key1], label=key1, linewidth=0.8, markersize=2)
        count += 1
    
    plt.set_xlabel('Time(hrs)', fontsize=9)
    plt.set_ylabel('Normalized \nParameter Value', fontsize=9) 
    plt.set_axisbelow(True)
    plt.yaxis.grid(color='lightgray', linestyle='solid')
    handles, labels = plt.get_legend_handles_labels()
    if figcount == 2:
        lg=plt.legend(prop={'size':7}, ncol=6,  borderaxespad=0., edgecolor='black', bbox_to_anchor=(1.1,1.65))
    figcount += 1

        

Figure.subplots_adjust(wspace=0.18, hspace=0.3)

PDF.savefig(Figure, bbox_inches='tight')
PDF.close()  
