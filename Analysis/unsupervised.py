import pandas as pd
import os
import math
from tqdm import tqdm
import numpy as np
import sys
##needed for debugging
sys.path.append('.')
from Database.db_api import Report_Extractor
from Analysis.functions import position_num_map, frequency_transformation

from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

rpt = Report_Extractor()
df = rpt.get_player_matches('Premiership', 2022)

#some cleaning
cols_with_data = [col for col in df.columns if not df[col].isna().all()]
df = df[cols_with_data]

df= df[df['position_num'] > 0]
df = df[df['position_num'] < 16]

df=df[df['mins_played']>10]

for col in df.columns:
    df[col] = pd.to_numeric(df[col]) 

features = df.columns[4:]

X = np.array(df[features])

pipe = Pipeline([('scaler', StandardScaler()),
                 ('PCA', PCA(n_components=2)),
                 ('kmean' ,KMeans(n_clusters=2, random_state=0))])

pca = pipe[:-1].fit(X)
reduced_data = pca.transform(X)
kmean = pipe.fit(X)
pos_labels = np.array(df['position_num'])


print(
    "explained variance ratio (first two components): %s"
    % str(pca[-1].explained_variance_ratio_)
)

import matplotlib.pyplot as plt
fig, ax = plt.subplots()
scatter = ax.scatter(reduced_data[:, 0], reduced_data[:, 1], marker=".", c = pos_labels, label = pos_labels)
ledgend = ax.legend(*scatter.legend_elements(),
                    loc="upper right", title="Classes")

centroids = kmean[-1].cluster_centers_
plt.scatter(
    centroids[:, 0],
    centroids[:, 1],
    marker="x",
    s=169,
    linewidths=3,
    color="r",
    zorder=10,
)

plt.xlabel("PC0")
plt.ylabel("PC1")
plt.show()



#3D PCA
pipe = Pipeline([('scaler', StandardScaler()),
                 ('PCA', PCA(n_components=3)),
                 ('kmean' ,KMeans(n_clusters=3, random_state=0))])

pca = pipe[:-1].fit(X)
reduced_data = pca.transform(X)
kmean = pipe.fit(X)
pos_labels = np.array(df['position_num'])


print(
    "explained variance ratio (first three components): %s"
    % str(pca[-1].explained_variance_ratio_)
)

print('of which the largest weighed feature is')
for i in range(0, len(pca[-1].components_)):
    print('PC-%s : ' % str(i), features[pca[-1].components_[i].argmax()])

import matplotlib.pyplot as plt
fig = plt.figure(1, figsize=(8, 6))
ax = fig.add_subplot(111, projection="3d", elev=-150, azim=110)
scatter = ax.scatter(reduced_data[:, 0], reduced_data[:, 1], reduced_data[:, 2], marker=".", c = pos_labels, label = pos_labels)
ledgend = ax.legend(*scatter.legend_elements(),
                    loc="upper right", title="Classes")

centroids = kmean[-1].cluster_centers_
ax.scatter(
    centroids[:, 0],
    centroids[:, 1],
    centroids[:, 2],
    s = 169,
    marker="x",
    linewidths=3,
    color="r",
    zorder=10,
)

plt.xlabel("PC0")
plt.ylabel("PC1")
ax.set_zlabel("PC2")
plt.show()


#Try for 10 PCA

pipe = Pipeline([('scaler', StandardScaler()),
                 ('PCA', PCA(n_components=10)),
                 ('kmean' ,KMeans(n_clusters=10, random_state=0))])

pca = pipe[:-1].fit(X)
reduced_data = pca.transform(X)
kmean = pipe.fit(X)

print(
    "explained variance ratio (first ten components): %s"
    % str(pca[-1].explained_variance_ratio_)
)

print(sum(pca[-1].explained_variance_ratio_))

print('of which the largest weighed feature is')
for i in range(0, len(pca[-1].components_)):
    print('PC-%s : ' % str(i), features[pca[-1].components_[i].argmax()])