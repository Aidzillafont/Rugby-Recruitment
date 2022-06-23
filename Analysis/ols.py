import statsmodels.api as sm
from statsmodels.formula.api import ols
import pandas as pd
import os
import math
from tqdm import tqdm
import numpy as np
import sys
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

#map positons
df['position'] = list(map(position_num_map, df['position_num']))

model = ols('tries ~ C(position)', data=df).fit()

anova_table = sm.stats.anova_lm(model, typ=2)
model.summary()

model = ols('tackles_made ~ C(position)', data=df).fit()

anova_table = sm.stats.anova_lm(model, typ=2)
model.summary()


model = ols('lineouts_won ~ C(position)', data=df).fit()

anova_table = sm.stats.anova_lm(model, typ=2)
model.summary()


model = ols('meters_made ~ C(position)', data=df).fit()

anova_table = sm.stats.anova_lm(model, typ=2)
model.summary()
