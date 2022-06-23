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

features = df.columns[4:-1]

label = 'position_num'

all_variables = [label, *features]


### Pearson correlation between positions and variables #####
corr_df = df[all_variables].corr()
np.fill_diagonal(corr_df.values, 0)

corr_df['position_num'].sort_values()

#checking max correlations
for feat in features:
    print(feat, corr_df[feat].max())

#for each position check high correlated feature varables
corr_dict = {}
for i in range(1,16):
    df_i  = df[df[label]==i]
    corr_i = df_i[features].corr()
    np.fill_diagonal(corr_i.values, 0)
    corr_dict[i] = corr_i

######## LDA #########
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
