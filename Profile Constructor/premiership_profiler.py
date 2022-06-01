import pandas as pd
import os
import math
from tqdm import tqdm
import numpy as np


filepath = os.getcwd() + '\\Data Cleaners\\Cleaner_Data\\premiership_matches.csv'
df = pd.read_csv(filepath, index_col=0)

# transformation for reletive to minutes played as per lit review
# after checking lit review transformation there seemed to be an error plot
# some case where the player played for less than 5 minutes you get some large multiplications
# might be worth removing those instances or finding a better transformation
def frequency_per80mransformation(x):
    #last minute subs
    x[1] = 5 if x[1] <= 5 else x[1]

    q = 80/float(x[1])
    return( (float(x[0])*q)/(math.log10(q)+1))

#Apply transformation for minutes played to in game data
cols_per80mo_per80mransform = ['M', 'C', 'P', 'T', 'MT', 'TW', 'TC', 'DB', 'TA', 'O', 'CB', 'LW', 'LS']

for col in tqdm(cols_per80mo_per80mransform):
    df['{0}_per80m'.format(col)] = df[[col,'min_played']].apply(frequency_per80mransformation, axis=1)


#create ratios of in game data where possible
df['Meters_per_Carry_per80m'] =  df['M_per80m']/df['C_per80m']
df['%Successful_per80mackles_per80m'] = df['T_per80m']/(df['T_per80m']+df['MT_per80m'])
df['%Turnovers_Won_per80m'] = df['TW_per80m']/(df['TW_per80m']+df['TC_per80m'])
#TODO: add a lineout total in game for each player in opposition and side
df['DB_per_Break_per80m']= df['DB_per80m']/df['C_per80m']


#clean some of the new features
df['DB_per_Break_per80m'].replace([np.inf, -np.inf], 0, inplace=True)
df.update(df[['DB_per_Break_per80m','Meters_per_Carry_per80m','%Successful_per80mackles_per80m','%Turnovers_Won_per80m']].fillna(0))

#replace position with most common position played
df_modes = df.groupby(['PlayGuid'])['pos_num'].agg(lambda x: x.value_counts().index[0])
df = df.merge(df_modes, on=['PlayGuid'], how='left')

save_path = os.getcwd() + '\\Profile Constructor\\Profile_Data\\premiership_profile.csv'

df.to_csv(save_path)

#take only players with 5 games
df_new = df.groupby('PlayGuid').filter(lambda x: len(x) >5)


#get mean and std
features = ['M_per80m', 'C_per80m', 'P_per80m', 'T_per80m', 'MT_per80m', 'TW_per80m', 
            'TC_per80m', 'DB_per80m', 'TA_per80m', 'O_per80m', 'CB_per80m', 'LW_per80m', 'LS_per80m',
            'DB_per_Break_per80m','Meters_per_Carry_per80m','%Successful_per80mackles_per80m','%Turnovers_Won_per80m']
df_profile_dist = df_new.groupby(['PlayGuid','pos_num_y'])[features].agg(['mean','std'])

save_path = os.getcwd() + '\\Profile Constructor\\Profile_Data\\premiership_profile_dist.csv'

df_profile_dist.to_csv(save_path)