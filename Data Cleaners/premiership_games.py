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
        'p_name':'name',
        'M':'meters_made',
        'C':'carries',
        'P':'passes_made',
        'T':'tackles_made',
        'MT':'missed_tackles',
        'TW':'turnovers_won',
        'TC':'turnovers_conceded',
        'DB':'defemders_beaten',
        'TA':'try_assists',
        'O':'offloads',
        'CB':'clean_breaks',
        'LW':'lineouts_won',
        'LS':'lineouts_stolen',
        }
    try:
        return name_dict[x]
    except KeyError:
        return x

def check_for_duplicates(master_dict):
#duplicates from scraping can only appear sequentially
    for i in range(1,158):
        if isinstance(master_dict[i], str):
            print(i, master_dict[i], sep=':  ')
            continue
        if isinstance(master_dict[i-1], str):
            continue

        if master_dict[i]['FT_Score']==master_dict[i-1]['FT_Score']:
            print(i, 'Possible Dupe', sep=':  ')

def extract_sub_data(Pos_Player_Array):
    #https://www.premiershiprugby.com/match-report/match-report-leicester-tigers-34-19-exeter-chiefs#report
    #weird inconsistancy in subbing on site double entries.
    #so we will always take last entry as those line up correctly
    #possible given issue where player will be subbed and not captured on site
    sub_flag = False
    p_name = []
    pos_num = []
    min_played = []
    is_sub = []
    for pos, player in Pos_Player_Array:
        #check if we are in replacements section
        if player == 'Replacements':
            sub_flag = True
            p_name.append(player)
            min_played.append(-1)
            is_sub.append(-1)
            pos_num.append(-1)
            continue

        subs = player.split('  ')

        #check if there are any subs
        if len(subs) == 1: #no subs
            p_name.append(subs[0])
            min_played.append(80)

            #issue where some subs do not have replacements data on site
            #Note on site they will populate sub data with players not subbed
            # when there is no sub. These players will be caught here and removed
            # by clean_df at end
            if sub_flag:
                #this -1 signifies not subbed in player to be removed
                is_sub.append(-1)
                pos_num.append(-1)
                continue

            is_sub.append(0)
            pos_num.append(int(pos))
            continue

        if sub_flag:
            p_name.append(subs[0])
            min_played.append(80 - int(subs[-1].strip("'")))
            is_sub.append(1)
            #find position of sub
            try:
                pos_num.append(pos_num[p_name.index(subs[-2])])
            except: #in the case of a resub
                pos_num.append([i for i,item in enumerate(Pos_Player_Array) if subs[-2] in item[1]][0])
            continue

        p_name.append(subs[0])
        #second split here since website has some small inconcistancies in formatting
        min_played.append(int(subs[-1].split(' ')[-1].strip("'")))
        is_sub.append(0)
        pos_num.append(int(pos))

    return(p_name, min_played, is_sub, pos_num)

def lookup_PlayGuid_list(p_names_df, list_ids):
    p_names, player_ids = zip(*list_ids)
    PlayGuids = []
    for p_name in p_names_df:
        try:
            PlayGuid_link = player_ids[p_names.index(p_name)]
            PlayGuid = PlayGuid_link.split('=')[1]
        except ValueError: #take player from relitave positon when lookup fails
            PlayGuid_link = player_ids[np.where(p_names_df==p_name)[0][0]]
            PlayGuid = PlayGuid_link.split('=')[1]

        PlayGuids.append(PlayGuid)
    return(PlayGuids)

def create_dict_special(special_list, at_home):
    headers = special_list[2]
    side_details = special_list[at_home]
    dict_lst = {h: d for h, d in zip(headers, side_details)}
    return dict_lst

def add_target_values(dict_key, dict_lst, df_col, df):
    #dictonary of known player miss spelling
    spelling = { 'Sam Lewis': 'Samuel Lewis',
                'Melani Nanai Vai': 'Melani Nanai',
                'Rus Tuima': 'Rusiate Tuima',
                'Matty Proctor': 'Matt Proctor',
                'Dan Thomas': 'Daniel Thomas',
                'Dan du Preez': 'Daniel du Preez',
                'Dom Morris': 'Dominic Morris',
                'Jamie Shillcock': 'James Shillcock',
                'Theo McFarland': 'Theodore McFarland',
                'Matt Cornish': 'Matthew Cornish',
                'Val Rapava Ruskin': 'Val Rapava-Ruskin',
                'Seb Atkinson': 'Sebastien Atkinson',
                'Elliott Obatoyinbo': 'Elliot Obatoyinbo',
                'Semi Radradra Waqavatu': 'Semi Radradra',
        }
    #penos
    try:
        players = [[p.split(',')[0], len(p.split(','))-1]for p in dict_lst[dict_key]]

        for p in players:
            #player name not recorded 
            if len(p[0]<=3):
                continue

            #player name not found
            if p[0] not in df['name'].values:
                try:
                    df.loc[df['name'] == spelling[p[0]]] = p[1]
                except:
                    print('Cannot find player {0}'.format(p[0]))
            else:
                df.loc[df['name'] == p[0], df_col] = p[1]
    except:
        #if no penalty goals in game
        pass

def clean_df(df, list_ids, at_home, target_details):
    df['at_home'] = at_home

    #determine minutes played and subs and add to dataframe
    p_name, min_played, is_sub, pos_num = extract_sub_data(df[['Pos','Player']].values)
    df['name'] = p_name
    df['mins_played'] = min_played
    df['is_sub'] = is_sub
    df['position_num'] = pos_num 

    #remove replacements column
    df.drop([p_name.index('Replacements')], inplace=True)

    #add in player ids
    df['playguid'] = lookup_PlayGuid_list(df['name'].values, list_ids)

    #drop reformatted columns
    df.drop(['Pos', 'Player'], axis=1, inplace=True)

    #fill in 0s
    df = df.replace('-',0)

    #rename columns for database
    df.columns = map(renaming_fun, df.columns)

    #add target detaild for penos, tries and convos
    dict_lst = create_dict_special(target_details, at_home)

    df['penalty_goals'] = 0
    add_target_values('Penalties',dict_lst, 'penalty_goals', df)

    df['tries'] = 0
    add_target_values('Tries',dict_lst, 'tries', df)
    #add_target_values('Penalty Tries',dict_lst, 'tries', df)

    df['conversions'] = 0
    add_target_values('Conversions',dict_lst, 'conversions', df)

    #remove players who did not play or we dont know for how long
    df = df[df['is_sub'] >= 0]

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
    insert_dict = {'name': 'Premiership',
                   'year': int(year)}
    comp = db_tool.insert(table, **insert_dict)

    for i in tqdm(range(0,len(loaded_dict))):
        #skip empty game data
        if isinstance(loaded_dict[i], str):
            print(i, loaded_dict[i], sep=':  ')
            continue

        #Match Details
        match_dict = dict((k, loaded_dict[i][k]) for k in ('match_date', 'home_team', 'away_team', 'FT_Score', 'HT_Score'))
        table = 'Matches' 
        p_table = 'Players'
        pm_table = 'Player_Matches'
        insert_dict = {'idComp': comp[0]['idComp'],
                       'date': dt.strptime(match_dict['match_date'],  '%A %d %B %Y'),
                       'home': match_dict['home_team'],
                       'away': match_dict['away_team'],
                       'FT_Score': match_dict['FT_Score'],
                       'HT_Score': match_dict['HT_Score'],
                       }
        match = db_tool.insert(table, **insert_dict)

        #home
        df1 = clean_df(loaded_dict[i]['home_df'], loaded_dict[i]['home_player_ids'],
                      1, loaded_dict[i]['target_details'])

        player_dict_list = df1[['playguid','name']].T.to_dict()
        player_match_dict_list = df1.drop(['name', 'playguid'], axis=1).T.to_dict()

        for j in range(0,len(player_dict_list)):
            player = db_tool.insert(p_table, **player_dict_list[j])
            #player match id
            id_dict = { 'idPlayer': player[0]['idPlayer'] , 'idMatch': match[0]['idMatch'] }
            insert_dict = {**id_dict, **player_match_dict_list[j]}
            db_tool.insert(pm_table, **insert_dict)
    
        #legacy
        list_of_dfs.append(df1)

        #away
        df2 = clean_df(loaded_dict[i]['away_df'], loaded_dict[i]['away_player_ids'], 
                       0, loaded_dict[i]['target_details'])

        player_dict_list = df2[['playguid','name']].T.to_dict()
        player_match_dict_list = df2.drop(['name','playguid'], axis=1).T.to_dict()

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


pickle_path = os.getcwd() + '\\Scrapers\\Scraped Data\\premiership_matches.pkl'
with open(pickle_path, 'rb') as f:
    loaded_dict = pickle.load(f)

master_df = load_to_db(2022, loaded_dict)

save_path =  os.getcwd() + '\\Data Cleaners\\Cleaner_Data\\premiership_matches.csv'

master_df.to_csv(save_path)


