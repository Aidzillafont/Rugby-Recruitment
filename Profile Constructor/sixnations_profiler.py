import pandas as pd
import os
import math
from tqdm import tqdm
import numpy as np


filepath = os.getcwd() + '\\Data Cleaners\\Cleaner_Data\\sixnations_matches.csv'
df = pd.read_csv(filepath, index_col=0)

def frequency_transformation(x):
    #last minute subs
    x[1] = 5 if x[1] <= 5 else x[1]

    q = 80/float(x[1])
    return( (float(x[0])*q)/(math.log10(q)+1))


#Apply transformation for minutes played to in game data
cols_to_transform = ['T','TA','C','P','DG','M','CA','MK','PM','O','BTs','Kon','TM','MT','TW','TC','HE','PC','OPC','SPC','LW','LS','YC','RC']

for col in tqdm(cols_to_transform):
    df['{0}_per80m'.format(col)] = df[[col,'MP']].apply(frequency_transformation, axis=1)


#Tackle success % is inconsistant on site with figures
#see number 7 on welsh team TM MT
#https://www.sixnationsrugby.com/report/conway-at-the-double-as-ireland-defeat-wales-in-dublin#match-stats
# so i will create my own based on teasformation of TM and MT

df['TS(%)_per80m'] = df['TM_per80m']/(df['TM_per80m']+df['MT_per80m'])
df['TW(%)_per80m'] = df['TW_per80m']/(df['TW_per80m']+df['TC_per80m'])
df['MpCA_per80m'] = df['M_per80m']/df['CA_per80m']

#replace position with most common position played
df_modes = df.groupby(['PlayGuid'])['pos_num'].agg(lambda x: x.value_counts().index[0])
df = df.merge(df_modes, on=['PlayGuid'], how='left')

save_path = os.getcwd() + '\\Profile Constructor\\Profile_Data\\sixnations_profile.csv'
df.to_csv(save_path)


features = ['{0}_per80m'.format(col) for col in cols_to_transform]
features.extend(['TS(%)_per80m','TW(%)_per80m','MpCA_per80m'])

#take only players with more than 3 games
df_new = df.groupby('PlayGuid').filter(lambda x: len(x) >3)

df_profile_dist = df_new.groupby(['PlayGuid','pos_num_y'])[features].agg(['mean','std'])

#merge levels of columns
df_profile_dist.columns = df_profile_dist.columns.map('|'.join).str.strip('|')


save_path = os.getcwd() + '\\Profile Constructor\\Profile_Data\\sixnations_profile_dist.csv'

df_profile_dist.to_csv(save_path)

