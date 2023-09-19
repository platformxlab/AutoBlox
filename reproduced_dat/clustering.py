import json
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
import math
import matplotlib.pyplot as plt
import matplotlib

f = open("../log/X_new.dat", "r")
X_new = np.array(json.loads(f.read()))

from matplotlib.patches import Ellipse
from matplotlib import transforms

matplotlib.rcParams.update({'font.family': 'serif'})


print("clustering figure...")
def confidence_ellipse(x, y, ax,  n_std=2.5, facecolor='none', **kwargs):
    """
    Create a plot of the covariance confidence ellipse of `x` and `y`

    Parameters
    ----------
    x, y : array_like, shape (n, )
        Input data.

    ax : matplotlib.axes.Axes
        The axes object to draw the ellipse into.

    n_std : float
        The number of standard deviations to determine the ellipse's radiuses.

    Returns
    -------
    matplotlib.patches.Ellipse

    Other parameters
    ----------------
    kwargs : `~matplotlib.patches.Patch` properties
    """
    if x.size != y.size:
        raise ValueError("x and y must be the same size")

    cov = np.cov(x, y)
    pearson = cov[0, 1]/np.sqrt(cov[0, 0] * cov[1, 1])
    # Using a special case to obtain the eigenvalues of this
    # two-dimensionl dataset.
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    ellipse = Ellipse((0, 0),
        width=ell_radius_x * 2,
        height=ell_radius_y * 2,
        facecolor=facecolor,
        **kwargs)
    # Calculating the stdandard deviation of x from
    # the squareroot of the variance and multiplying
    # with the given number of standard deviations.
    scale_x = np.sqrt(cov[0, 0]) * n_std
    mean_x = np.mean(x)

    # calculating the stdandard deviation of y ...
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_y = np.mean(y)

    transf = transforms.Affine2D() \
        .rotate_deg(45) \
        .scale(scale_x, scale_y) \
        .translate(mean_x, mean_y)

    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)


colors = ["green","red","darkorange","blue","#008b8b","black","orange","#fac205"]
colored = []

catcolor = {'AdsDataServer': 0,
 'AdspayLoad': 1,
 'LiveMapsBackEnd': 2,
 'YCSB': 3,
 'CloudStorage': 4,
 'TPCC': 5,
 'MapReduce': 6
}
import time
time1 = time.time()
markers =["o",  "^", "P", "+",  "X", "D","x","|"]
clustering = KMeans(n_clusters=6,random_state=0).fit(X_new)
time2 = time.time()
print(time2-time1)
from scipy import interpolate
from scipy.spatial import ConvexHull

fig, ax = plt.subplots(1, figsize=(5,2.5))
id2lab = ["Database","LiveMaps", "Advertisement", "SearchEngine", "BatchDataAnalytics", "KVStore"]
labcount = []
for i in range(0, len(X_new)):
    if clustering.labels_[i] not in labcount:
        labcount.append(clustering.labels_[i])
        plt.scatter(X_new[i,0], X_new[i,1],color=colors[clustering.labels_[i]],marker=markers[clustering.labels_[i]], label=id2lab[clustering.labels_[i]])
    else:
        plt.scatter(X_new[i,0], X_new[i,1],color=colors[clustering.labels_[i]],marker=markers[clustering.labels_[i]])

    
point_set = [[[],[]],[[],[]],[[],[]],[[],[]],[[],[]],[[],[]]]
for i in range(0, len(X_new)):
    point_set[clustering.labels_[i]][0].append(X_new[i,0].tolist())
    point_set[clustering.labels_[i]][1].append(X_new[i,1].tolist())

for i in range(6):
    confidence_ellipse(np.array(point_set[i][0]), np.array(point_set[i][1]), ax, facecolor=colors[i], alpha=0.5)
plt.xlim(-90,100)
plt.ylim(-45,100)

ax.tick_params(axis='both', which='major', labelsize=9)
ax.tick_params(axis='both', which='minor', labelsize=9)
plt.legend( loc = 'upper left', ncol=2, fontsize=9, borderaxespad=0., frameon=False)
plt.xlabel("Factor 1",fontsize=9)
plt.ylabel("Factor 2",fontsize=9)
fig.savefig("clustering.pdf", bbox_inches='tight')
