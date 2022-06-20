import pandas as pd
import os
import math
from tqdm import tqdm
import numpy as np
import sys
##needed for debugging
sys.path.append('.')
from Database.db_api import Report_Extractor

def home_win_lose_or_draw(x):
    result = [int(score) for score in x.split('-')]
    if result[0]>result[1]:
        return 1 #home win
    elif result[0]<result[1]:
        return 0 #home lose
    else:
        return 0.5 #draw

def player_actual_score(x):
    if x[1]==0.5: #draw
        return 0.5
    elif x[0] == x[1]: #home player 1 home win 1/ away player 0 home lose 0
        return 1
    elif x[0] != x[1]: #home player 1 home lose 0/away player 0 home win 1
        return 0

def calc_elo_delta(Oa, Ob, Sa, Sb):
    Ea = Oa/(Oa+Ob)
    Eb = Ob/(Oa+Ob)
    elo_delta_a = 32*(Sa-Ea)
    elo_delta_b = 32*(Sb-Eb)
    return (elo_delta_a, elo_delta_b)

rpt = Report_Extractor()

comp = 'Six Nations'
year = 2022

df_m = rpt.get_matches(comp, year)
df_pm = rpt.get_player_matches(comp, year)

df_m['home_wld'] = df_m['FT_Score'].apply(lambda x: home_win_lose_or_draw(x))

plyr_lst = [x for x in df_pm['idPlayer'].unique()]
df_p = rpt.get_players_from_list(plyr_lst)

df = pd.merge(df_pm, df_m, left_on='idMatch', right_on='idMatch')
df = pd.merge(df, df_p, left_on='idPlayer', right_on='idPlayer')
#start all players at 1200
df['elo_rating'] = 1200
#elo score is updated by R* = R + 32*(S-E)
#S is actual score i.e 1 for win, 0.5 for draw and 0 for lose
#E is expected score calculated by 
#E = Q/Q+Qo 
#Q = 10^(R/100) and Qo = 10^(Ro/400)
#needs to be done once
df['S_Score'] = df[['at_home','home_wld']].apply(player_actual_score, axis=1)
#update after each match
df['Q_score'] = 10**(df['elo_rating'].values/400)

for idMatch in df['idMatch'].unique():
    #update all Q scores on latest elos
    df['Q_score'] = 10**(df['elo_rating'].values/400)
    #get match events
    df_match = df[df['idMatch']==idMatch]
    for pos_num in range(1,16):
        #get players for position
        df_players = df_match[df_match['position_num'] == pos_num]
        df_grp = df_players[['at_home','Q_score','S_Score']].groupby(['at_home']).agg('mean')
        delta_a, delta_h = calc_elo_delta(df_grp['Q_score'][0], df_grp['Q_score'][1], df_grp['S_Score'][0], df_grp['S_Score'][1])
        #Need to update the PLAYERS ELO for all games....multiple updates here should update player table really
        home_idx = df['idPlayer'].isin(df_players['idPlayer'][df_players['at_home']==1])
        away_idx = df['idPlayer'].isin(df_players['idPlayer'][df_players['at_home']==0])
        df.loc[home_idx, 'elo_rating'] += delta_h
        df.loc[away_idx, 'elo_rating'] += delta_a
    #TODO: add deltas to elo


df.to_csv('players_elo.csv')

#possible extensions weight player delta by mins played and features


