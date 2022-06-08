import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime as dt
from tqdm import tqdm
import sys
##needed for debugging
sys.path.append('.')
from Database.db_api import db_api


def renaming_fun(x):
    #this fuction renames columns in df to better match db for upload later
    name_dict = {
        'Player':'name',
        'MP':'mins_played',
        'T':'tries',
        'TA':'try_assists',
        'C':'conversions',
        'P':'penalty_goals',
        'DG':'drop_goals',
        'M':'meters_made',
        'CA':'carries',
        'PK(%)':'possession_kicked_pct',
        'MK':'meters_kicked',
        'BH(%)':'balls_played_by_hand',
        'PM':'passes_made',
        'O':'offloads',
        'BTs':'broken_tackles',
        'Kon':'knock_ons',
        'TM':'tackles_made',
        'MT':'missed_tackles',
        'TS(%)':'tackle_success_pct',
        'DT(%)':'dominant_tackles_pct',
        'TW':'turnovers_won',
        'TC':'turnovers_conceded',
        'HE':'handling_errors',
        'PC':'pens_conceded',
        'OPC':'offside_penalties',
        'SPC':'scrum_penalties',
        'LW':'lineouts_won',
        'LS':'lineouts_stolen',
        }
    try:
        return name_dict[x]
    except KeyError:
        return x

def check_for_duplicates(master_dict):
#duplicates from scraping can only appear sequentially
    for i in range(1,len(master_dict)):
        if isinstance(master_dict[i], str):
            print(i, master_dict[i], sep=':  ')
            continue
        if isinstance(master_dict[i-1], str):
            continue

        if master_dict[i]['FT_Score']==master_dict[i-1]['FT_Score']:
            print(i, 'Possible Dupe', sep=':  ')

def get_position_subsitution(x, on_reps, off_reps, df):
    #ignore starting players
    if x[1]<=15:
        return(x[1])

    #find player replaced
    #sometimes timeline does not have substitution data for player 
    try:
        ind_rep = on_reps.index(x[0])
    except ValueError:
        return(-1)

    off_rep = off_reps[ind_rep]

    #get replacing postion
    pos_num = df[df['Player']==off_rep].iloc[0]['position_num']

    return(pos_num)

def get_on_off_replacements(replacements):
    #split replacements in to on off
    #replacements = loaded_dict[0]['replacements']
    replacemnt_cleaner = [r.strip('\n').replace(' \n ', ',').replace('\n','').split(',') for r in replacements]
    on_off_replacement = [[r[0].strip(), r[1].strip()]for r in replacemnt_cleaner]
    return(zip(*on_off_replacement))
    
def get_PlayGuid(player_ids):
    p_name, PlayGuid_links = zip(*player_ids)
    PlayGuid = [l.split('=')[1].split('&')[0] for l in PlayGuid_links]
    return(PlayGuid)

def create_clean_df(dict, at_home):
    team = 'home' if at_home==1 else 'away'

    df = dict['{}_df'.format(team)]
    df['at_home'] = at_home

    #clean table
    cols_to_drop =[col for col in df.columns if 'Unnamed' in col]
    df = df.drop(cols_to_drop, axis=1)
    df = df[df['Player']!='Replacements']

    on_reps, off_reps = get_on_off_replacements(dict['replacements'])

    #Clean player name and add positions for subs
    df['position_num'] = [int(p.split('  ')[0]) for p in df['Player']]
    df['Player'] = [p.split('  ')[1] for p in df['Player']]
    df['is_sub'] = [1 if p>15 else 0 for p in df['position_num']]
    df['position_num'] = df[['Player','position_num']].apply(lambda x: get_position_subsitution(x, on_reps, off_reps, df), axis=1)

    df['playguid'] = get_PlayGuid(dict['{0}_player_ids'.format(team)])

    #rename columns for database
    df.columns = map(renaming_fun, df.columns)

    #remove players who did not play
    df = df[df['mins_played'] != 0]

    #reset index
    df = df.reset_index(drop=True)
    return(df)

def load_to_db(year, loaded_dict):
    #connect to db
    db_tool = db_api()

    #legacy
    list_of_dfs = []

    #create compitition record
    table = 'Comps' 
    insert_dict = {'name': 'Six Nations',
                   'year': int(year)}
    comp = db_tool.insert(table, **insert_dict)

    for i in tqdm(range(0,len(loaded_dict))):
        #Match Details
        match_dict = dict((k, loaded_dict[i][k]) for k in ('match_date', 'home_team', 'away_team', 'FT_Score', 'HT_Score'))
        table = 'Matches' 
        p_table = 'Players'
        pm_table = 'Player_Matches'
        insert_dict = {'idComp': comp[0]['idComp'],
                       'date': dt.strptime(match_dict['match_date'], '%d %b %Y'),
                       'home': match_dict['home_team'],
                       'away': match_dict['away_team'],
                       'FT_Score': match_dict['FT_Score'],
                       'HT_Score': match_dict['HT_Score'],
                       }
        match = db_tool.insert(table, **insert_dict)

        #home
        df1 = create_clean_df(loaded_dict[i], 1)

        player_dict_list = df1[['playguid','name']].T.to_dict()
        player_match_dict_list = df1.drop(['name','YC','RC','playguid'], axis=1).T.to_dict()

        for j in range(0,len(player_dict_list)):
            player = db_tool.insert(p_table, **player_dict_list[j])
            #player match id
            id_dict = { 'idPlayer': player[0]['idPlayer'] , 'idMatch': match[0]['idMatch'] }
            insert_dict = {**id_dict, **player_match_dict_list[j]}
            db_tool.insert(pm_table, **insert_dict)
    
        #legacy
        list_of_dfs.append(df1)

        #away
        df2 = create_clean_df(loaded_dict[i], 0)

        player_dict_list = df2[['playguid','name']].T.to_dict()
        player_match_dict_list = df2.drop(['name','YC','RC','playguid'], axis=1).T.to_dict()

        for j in range(0,len(player_dict_list)):
            player = db_tool.insert(p_table, **player_dict_list[j])
            #player match id
            id_dict = { 'idPlayer': player[0]['idPlayer'] , 'idMatch': match[0]['idMatch'] }
            insert_dict = {**id_dict, **player_match_dict_list[j]}
            db_tool.insert(pm_table, **insert_dict)

        #legacy
        list_of_dfs.append(df2)

    #legacy
    master_df = pd.concat(list_of_dfs)
    master_df.reset_index(inplace = True, drop=True)

    return master_df

#load file
pickle_path = os.getcwd() + '\\Scrapers\\Scraped Data\\sixnation_matches.pkl'
with open(pickle_path, 'rb') as f:
    loaded_dict = pickle.load(f)

#check for dupes
check_for_duplicates(loaded_dict)

master_df = load_to_db(2022, loaded_dict)

save_path =  os.getcwd() + '\\Data Cleaners\\Cleaner_Data\\sixnations_matches.csv'

master_df.to_csv(save_path)


#Cut off time played i.e less than 10 minutes not included
#Look into storage solutions better than csv/pkl
# for website scrapes pickle since data may change out of our control
# Those pickles then can be transformed and loaded into mySQL to facilitae joins and master stat tables
#Think about outcome target
#front end thoughts (dash board type) Power BI
#direction of project to companies. Opta 
#resample not a first course of action need a good reason
#try simple classifiers