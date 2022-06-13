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

rpt = Report_Extractor()
df = rpt.get_player_matches('Premiership', 2022)

#find columns not all na
cols_with_data = [col for col in df.columns if not df[col].isna().all()]
df = df[cols_with_data]
#remove position numbers that are not gathered correctly
df= df[df['position_num'] > 0]
df = df[df['position_num'] < 16]

#only keep examples where 20+ mins played
df = df[df['mins_played']>20]

#make numeric
for col in df.columns:
    df[col] = pd.to_numeric(df[col]) 

# tackle ratio
df['tackle_success'] = df['tackles_made']/df['missed_tackles']
# meters per carrie ratio
df['mpc'] = df['meters_made']/df['carries']

#
engineered_feat = ['tackle_success','mpc']
for e in engineered_feat:
    df[e].replace([np.inf, -np.inf], 0, inplace=True)
df.update(df[engineered_feat].fillna(0))

#this is a bit cheaty but helps accuracy espically for all rounders like flankers/centres
#df['is_forward'] = df['position_num'].apply(lambda x: 1 if x < 9 else 0)

#map position numbers
df['position'] = list(map(position_num_map, df['position_num']))

#removing flankers and centres
#df = df[df['position'] != 'Centre']
#df = df[df['position'] != 'Flanker']

#### No transform ####
#features = df.columns[3:-5]

#### minutes played transform ####
features = df.columns[4:-1]

for feature in tqdm(features):
    df[feature] = df[[feature,'mins_played']].apply(frequency_transformation, axis=1)

#### Profile with minutes played tranform ####

#df = df.groupby(['idPlayer','position'])[features].agg(['mean'])
##rename columns and reset index after grouping
#df.columns = df.columns.levels[0]
#df = df.reset_index(drop=False)

label = ['position']

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

#Train Test Split
X, y = df[features], df[label]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=69)


#Pipeline
pipe = Pipeline([('scaler', StandardScaler()),
                 ('rf', RandomForestClassifier(random_state=69, class_weight='balanced'))])

param_grid = {
    "rf__n_estimators": [100, 500],
    "rf__criterion": ['entropy'],
    "rf__max_depth": [4, 8, 12],
    "rf__max_features": ['auto','sqrt'],
    'rf__max_leaf_nodes': [16,32]
    }

cv = GridSearchCV( pipe, param_grid, n_jobs=-1, cv=10, verbose=10)
cv.fit(X_train, y_train.values.ravel())

print('The best score was: ', cv.best_score_, ' with the following parameters.\n')
print(cv.best_params_)

cv.best_params_

#make confusion matrix
import matplotlib.pyplot as plt
from sklearn.metrics import plot_confusion_matrix
plot_confusion_matrix(cv.best_estimator_, X_test, y_test)  
plt.xticks(rotation=90)
plt.show()

#really struggles with flankers and centres
# mixes up hookers with props

#scrum half and fly half easliy identified model
# Can resonably separate first/second row and number 8....some mix up between first and second row
# probablly down to second row players not perfoming well in line outs
# Somwtimes mis labels wings as full backs. probbably the wings who do not score tries
# Centres just a mixed bag 

df['position'].value_counts()
#using best params lets build a forest and extract important features

forest = RandomForestClassifier(random_state=69, class_weight='balanced', max_depth=8, criterion= 'entropy', max_features='auto', n_estimators=300)
forest.fit(X_train, y_train.values.ravel())

F_imp = [[f, imp] for f, imp in zip(list(features), list(forest.feature_importances_))]
df_F_imp = pd.DataFrame(F_imp, columns = ['feature', 'importance'])


import seaborn as sns
ax = sns.barplot(x="importance", y="feature", data=df_F_imp)
plt.show()

from sklearn.feature_selection import RFECV

#rfe = RFECV(estimator=forest, scoring='accuracy')

#rfe.fit(X_train, y_train.values.ravel())

## print a tree
from sklearn import tree
fig, axes = plt.subplots(nrows = 1,ncols = 1,figsize = (4,4), dpi=800)
tree.plot_tree(forest.estimators_[0],
               feature_names = features, 
               class_names=df['position'].unique(),
               filled = True)
plt.show()




#### KNN ####
from sklearn.neighbors import KNeighborsClassifier
#Pipeline
pipe = Pipeline([('scaler', StandardScaler()),
                 ('knn', KNeighborsClassifier())])

param_grid = {
    "knn__n_neighbors": [4,8,16],
    "knn__weights": ['uniform', 'distance'],
}


cv = GridSearchCV(pipe, param_grid, n_jobs=-1, cv=10, verbose=10)
cv.fit(X_train, y_train.values.ravel())

print('The best score was: ', cv.best_score_, ' with the following parameters.\n')
print(cv.best_params_)



#### XGB ####
from xgboost import XGBClassifier
xgbm_pipe = Pipeline([('scaler', StandardScaler()), ('xgbm', XGBClassifier())])

xgbm_para = {
            'xgbm__n_estimators':[500,1000,2000],
            'xgbm__max_depth':[8, 16, 32, 64],
            'xgbm__eta':[0.1,0.3,0.5] #test different learning rates to try to avoid local minima
            }

xgbm_gs = GridSearchCV(xgbm_pipe,xgbm_para, scoring="accuracy", n_jobs=-1, verbose=10)

##xgboost needs classes to be 0,1,2...
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
y_train_lab = le.fit_transform(y_train)

xgbm_gs.fit(X_train, y_train_lab)

print('The best score was: ', xgbm_gs.best_score_, ' with the following parameters.\n')
print(xgbm_gs.best_params_)
