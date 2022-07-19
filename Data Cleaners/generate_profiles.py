import pandas as pd
import os
import math
from tqdm import tqdm
import numpy as np
import sys
##needed for debugging
sys.path.append('.')
from Database.db_api import Report_Extractor
from Analysis.functions import frequency_transformation
from Analysis.elo_rating import add_elo_score

def renaming_fun(x):
    #this fuction renames columns in df to better match db for upload later
    name_dict = {
         'count': 'games_played',
         'position_num_y' : 'most_common_position_num',
         'tries_mean' : 'm_tries',
         'tries_std' : 's_tries',
         'try_assists_mean' : 'm_try_assist',
         'try_assists_std' : 's_try_assist',
         'conversions_mean' : 'm_conversions',
         'conversions_std' : 's_conversions',
        'penalty_goals_mean' : 'm_penalty_goals',
         'penalty_goals_std' : 's_penalty_goals',
         'meters_made_mean' : 'm_meters_made',
         'meters_made_std' : 's_meters_made',
         'carries_mean' : 'm_carries',
         'carries_std' : 's_carries',
         'passes_made_mean' : 'm_passes_made',
        'passes_made_std' : 's_passes_made',
         'offloads_mean' : 'm_offloads',
         'offloads_std' : 's_offloads',
         'tackles_made_mean' : 'm_tackles_made',
        'tackles_made_std' : 's_tackles_made',
         'missed_tackles_mean' : 'm_missed_tackles',
         'missed_tackles_std' : 's_missed_tackles',
        'turnovers_won_mean' : 'm_turnovers_won',
         'turnovers_won_std' : 's_turnovers_won',
         'turnovers_conceded_mean' : 'm_turnovers_conceded',
        'turnovers_conceded_std' : 's_turnovers_conceded',
         'lineouts_won_mean' : 'm_lineouts_won',
         'lineouts_won_std' : 's_lineouts_won',
        'lineouts_stolen_mean' : 'm_lineouts_stolen',
         'lineouts_stolen_std' : 's_lineouts_stolen',
         'defenders_beaten_mean' : 'm_defenders_beaten',
         'defenders_beaten_std' : 's_defenders_beaten',
         'clean_breaks_mean' : 'm_clean_breaks',
         'clean_breaks_std' : 's_clean_breaks',
         'elo_rating' : 'elo_score'
        }
    try:
        return name_dict[x]
    except KeyError:
        return x

def load_updates(df, rpt):
    #undo groupby re index and leveling
    try:
        df = df.reset_index('position_num_y')
    except:
        pass

    if df.columns.nlevels == 2:
        df.columns = df.columns.map('_'.join).str.strip('_')



    #map columns for sql
    df.columns = map(renaming_fun,df.columns)
    #replace nan with none for sql
    df = df.where(pd.notnull(df), None)

    #make into dict for SQL 
    dict = df.T.to_dict()

    for key, value in tqdm(dict.items()):
        where_dict = {'idPlayer': [key]}
        rpt.update('Players', value, **where_dict)
    
    return 0

rpt = Report_Extractor()

df = pd.DataFrame(rpt.find('Player_Matches', ['*'], true=True))

#loading scores
df['defense_score'] = (df['mins_played']/80)*pd.to_numeric(df['defense_score_team'])
df['attack_score'] = (df['mins_played']/80)*pd.to_numeric(df['attack_score_team'])
df['open_score'] = (df['mins_played']/80)*pd.to_numeric(df['open_score_team'])

df_scores = df.groupby(['idPlayer'])[['defense_score','attack_score','open_score']].mean()

#adding elo
df_m = pd.DataFrame(rpt.find('Matches', ['*'], true=True))
df_elo = add_elo_score(df_m, player_match_df=df)

cols_to_trans = ['tries','try_assists', 'conversions', 'penalty_goals', 
       'meters_made', 'carries', 'passes_made', 'offloads', 'tackles_made', 
       'missed_tackles', 'turnovers_won', 'turnovers_conceded', 'lineouts_won',
       'lineouts_stolen', 'defenders_beaten', 'clean_breaks']

for col in tqdm(cols_to_trans):
    df[col] = df[[col,'mins_played']].apply(lambda x: frequency_transformation(x), axis=1)

#replace position number with most common
df_modes = df.groupby(['idPlayer'])['position_num'].agg(lambda x: x.value_counts().index[0])
df = df.merge(df_modes, on=['idPlayer'], how='left')

#create df for mean and std of stats and game count
df_profile_dist = df.groupby(['idPlayer','position_num_y'])[cols_to_trans].agg(['mean','std'])
df_game_count= df.groupby(['idPlayer','position_num_y'])['mins_played'].agg(['count'])

#load profile and game count updates
load_updates(df_profile_dist, rpt)
load_updates(df_game_count, rpt)

#group and load elo rating 
df_grp_elo = df_elo.groupby(['idPlayer'])['elo_rating'].mean()

load_updates(df_grp_elo.to_frame('elo_score'), rpt)

#load scores 
load_updates(df_scores, rpt)