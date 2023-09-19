# from selectors import EpollSelector
import numpy as np
import matplotlib as PlotLib
import sys
import math
import matplotlib.pyplot as PyPlot
from matplotlib.backends.backend_pdf import PdfPages
import os
import json
import seaborn as sns

labelmapping = {"CS":"CloudStorage",
                "MR":"BatchDataAnalytics",
                "DB":"DataBase",
                "KV":"KVStore",
                "LM":"LiveMaps",
                "RC":"Recommendations",
                "WS":"WebSearch"}

f = open("fine_pruning.dat", "r")
coefficients = json.loads(f.read())
f.close()
# PlotLib.rcParams["font.family"] = 'Arial'
PlotLib.use('Agg')

PlotLib.rcParams['hatch.linewidth'] = 0.1
colors = ['#ff796c', '#fac205', '#95d0fc', '#96f97b']

sns.set(font_scale=0.4)


xticks = []
for key in coefficients:
    cat = key
    if key == "RC" or len(coefficients.keys()) == 1:
        for key1 in coefficients[cat]:
            pos = 0
            for item in xticks:
                if coefficients[cat][item] > coefficients[cat][key1]:
                    pos += 1
            xticks.insert(pos, key1)        
        break

keyorder = [ "CS","RC","LM", "KV","DB","MR","WS"]
threshold = 1e-3
data = []
yticks = []
for key in keyorder:
    if key not in coefficients:
        continue
    yticks.append(labelmapping[key])
    tmp = []
    for key1 in xticks:
        # if coefficients[key][key1] > threshold or coefficients[key][key1] < - threshold:
        tmp.append(coefficients[key][key1])
        # else:
        #     tmp.append(0)
    data.append(tmp)


figname = "fine_grained.pdf"

PDF = PdfPages(figname)
ax = sns.heatmap(np.array(data), xticklabels=xticks, yticklabels=yticks, cmap=PyPlot.get_cmap("seismic_r"),center=0.0, annot=True, fmt=".3f", cbar=False)
ax.set_xticklabels(xticks, fontsize=5, rotation=30, ha='right')
ax.set_yticklabels(yticks , fontsize=5, rotation=0, ha='right')
Figure = ax.get_figure()
Figure.set_size_inches(8, 1)
# PlotLib.rcParams.update({'font.family': 'serif'})
Figure.savefig(figname, bbox_inches='tight')
# PDF.savefig(Figure, bbox_inches='tight')
        


