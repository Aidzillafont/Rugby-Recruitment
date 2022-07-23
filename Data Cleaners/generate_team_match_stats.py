import pandas as pd
import os
import math
from tqdm import tqdm
import numpy as np
import sys
from sklearn.preprocessing import MinMaxScaler
##needed for debugging
sys.path.append('.')
from Database.db_api import Report_Extractor


def load_to_db(df):
    dict = df_for_upload.T.to_dict()

    for key, value in tqdm(dict.items()):

        where_dict = {'idPlayer':[value['idPlayer']],
                      'idMatch':[value['idMatch']]
                      }
        #remove where items
        value.pop('idPlayer')
        value.pop('idMatch')

        rpt.update('Player_Matches', value, **where_dict)

    return 0

def calc_team_score(df_matches, df_player_matches, score_type='defense'):
    score_types = ['attack', 'open', 'defense']
    if score_type not in score_types:
            raise ValueError("Invalid score type. Expected one of: %s" % sim_types)

    #ADDING SCALING TO ACTIONS MIGHT BE HELPFUL TO STOP CERTIAN ACTIONS DOMINATING
    #ALSO CHOICE OF FEATURES TO IN FORM SHOULD BE MEASURED SOMEWAY
    #ADDING WEIGHTS TO SUM MAY IMPROVE ACCURACY
    if score_type == 'defense':
        actions = ['tackles_made', 'missed_tackles', 'turnovers_won']
        #we reverse home and away here to map opposition score to teams defensive performance
        df_matches['0'] = df_matches['FT_Score'].str.split('-', expand=True)[0]
        df_matches['1'] = df_matches['FT_Score'].str.split('-', expand=True)[1]
    elif score_type == 'attack':
        actions = ['tries', 'try_assists', 'conversions', 'penalty_goals']
        #we DO NOT reverse home and away here to map opposition score to teams defensive performance
        df_matches['1'] = df_matches['FT_Score'].str.split('-', expand=True)[0]
        df_matches['0'] = df_matches['FT_Score'].str.split('-', expand=True)[1]
    elif score_type == 'open':
        actions = ['passes_made', 'meters_made', 'carries', 'defenders_beaten', 'clean_breaks', 'offloads']
        #we DO NOT reverse home and away here to map opposition score to teams defensive performance
        df_matches['1'] = df_matches['FT_Score'].str.split('-', expand=True)[0]
        df_matches['0'] = df_matches['FT_Score'].str.split('-', expand=True)[1]


    df_actions = df_player_matches.groupby(['idMatch', 'at_home'])[actions].agg('sum')
    df_actions = df_actions.reset_index()

    df_scores = df_matches[['idMatch', '0', '1']].melt(id_vars='idMatch')
    
    #convert and rename some columns
    df_scores.columns = ['idMatch', 'variable', 'Score']
    convert_dict = {'variable': np.int64,
                    'Score': np.float64,
                    }
    df_scores = df_scores.astype(convert_dict)

    df_full =  pd.merge(df_actions, df_scores, left_on=['idMatch', 'at_home'], right_on = ['idMatch','variable'])

    #scale data
    scaler = MinMaxScaler()
    df_scaled = pd.DataFrame(scaler.fit_transform(df_full), columns=df_full.columns)

    if score_type == 'defense':
        #invert missed tackles since its failed defensive action
        df_scaled['missed_tackles'] = 1/df_scaled['missed_tackles']
        m = df_scaled.loc[df_scaled['missed_tackles'] != np.inf, 'missed_tackles'].max()
        df_scaled['missed_tackles'].replace(np.inf,m,inplace=True)
        df_full['{0}_score'.format(score_type)] = df_scaled[actions].sum(axis=1)/ df_scaled['Score']
        return(df_full)
    else:
        df_full['{0}_score'.format(score_type)] = df_scaled[actions].sum(axis=1) #df_scaled['Score'] / define attack action of team
        return(df_full)

#log for high value 
rpt = Report_Extractor()

df = pd.DataFrame(rpt.find('Player_Matches', ['*'], true=True))
df_match = pd.DataFrame(rpt.find('Matches', ['*'], true=True))

df_defense = calc_team_score(df_match, df, score_type='defense')

df_attack  = calc_team_score(df_match, df, score_type='attack')

df_open  = calc_team_score(df_match, df, score_type='open')

df =  pd.merge(df, df_defense, left_on=['idMatch', 'at_home'], right_on = ['idMatch','at_home'])
df =  pd.merge(df, df_attack, left_on=['idMatch', 'at_home'], right_on = ['idMatch','at_home'])
df =  pd.merge(df, df_open, left_on=['idMatch', 'at_home'], right_on = ['idMatch','at_home'])


df_for_upload = df[['idPlayer', 'idMatch',
                    'tackles_made_y', 'missed_tackles_y', 'turnovers_won_y', 'defense_score', 
                    'tries_y', 'try_assists_y', 'conversions_y', 'penalty_goals_y', 'attack_score', 
                    'passes_made_y', 'meters_made_y', 'carries_y',  'open_score']]

df_for_upload.columns = ['idPlayer', 'idMatch',
                        'tackles_made_team', 'missed_tackles_team', 'turnovers_won_team', 'defense_score_team', 
                        'tries_team', 'try_assists_team', 'conversions_team', 'penalty_goals_team', 'attack_score_team', 
                        'passes_made_team', 'meters_made_team', 'carries_team',  'open_score_team']

#replace infs with max
for column in ['defense_score_team', 'attack_score_team', 'open_score_team']:
    m = df_for_upload.loc[df_for_upload[column] != np.inf, column].max()
    df_for_upload[column].replace(np.inf,m,inplace=True)

#replace nan with 0 
df_for_upload.replace(np.nan, 0, inplace=True)

#scale the scores to be between 0-1
scaler = MinMaxScaler()
df_for_upload_scaled = pd.DataFrame(scaler.fit_transform(df_for_upload), columns=df_for_upload.columns)

df_for_upload['defense_score_team'] = df_for_upload_scaled['defense_score_team']
df_for_upload['attack_score_team'] = df_for_upload_scaled['attack_score_team']
df_for_upload['open_score_team'] = df_for_upload_scaled['open_score_team']


##TODO: ADD COLUMNS TO SQL DB FOR TEAM STATS IN PLAYER_MATCH_TABLE
##TODO: ADD SIMILAR COLUMNS FOR SCORES FOR PLAYERS IN PLAYERS TABLE
## GIVE PLAYERS PART OF TEAM SCORE AND MAP THE PLAYERS AVERAGE SCORE TO PLAYERS TABLE

load_to_db(df_for_upload)




