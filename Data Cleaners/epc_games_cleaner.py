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
        'M':'meters_made',
        'Ca':'carries',
        'Pa':'passes_made',
        'Tk':'tackles_made',
        'MT':'missed_tackles',
        'TOW':'turnovers_won',
        'TAs':'try_assists',
        'O':'offloads',
        'CB':'clean_breaks',
        }
    try:
        return name_dict[x]
    except KeyError:
        return x

def extract_sub_data(Player_Array):
    sub_flag = False
    p_name = []
    pos_num = []
    min_played = []
    is_sub = []
    for p in Player_Array:
        #check if we are in replacements section
        if p == 'Replacements':
            sub_flag = True
            p_name.append(p)
            min_played.append(-1)
            is_sub.append(-1)
            pos_num.append(-1)
            continue

        subs = p.split('  ')

        if len(subs) == 2: #no subs
                p_name.append(subs[1])
                min_played.append(80)
                is_sub.append(0)
                pos_num.append(int(subs[0]))
                continue

        if sub_flag:
            p_name.append(subs[1])
            sub_time = subs[-1:][0].rsplit(' ', 1)[-1].strip("'")
            off_name = subs[-1:][0].rsplit(' ', 1)[0]
            min_played.append(80 - int(sub_time))
            is_sub.append(1)
            try:
                pos_num.append(pos_num[p_name.index(off_name)])
            except: # in case of resub
                pos_num.append([i for i,item in enumerate(Player_Array) if off_name in item][0])
            continue

        p_name.append(subs[1])
        min_played.append(int(subs[-1:][0].rsplit(' ', 1)[-1].strip("'")))
        is_sub.append(0)
        pos_num.append(int(subs[0]))     

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

def add_target_values(dict_key, dict_lst, df_col, df, name_lookup):
    #dictonary of known player miss spelling
    spelling = { 'O. du Toit': 'J. du Toit',
                'I. Tekori': 'J. Tekori',
                'A. Alo': 'B. Alo',
                'M. Patchell': 'R. Patchell',
                'W. Radradra': 'S. Radradra',
                'J. Reinach': 'C. Reinach',
                'E. Tuilagi': 'M. Tuilagi',
                'W. Twelvetrees': 'B. Twelvetrees',
                'W. Scannell': 'B. Scannell',
                'M. Wacokecoke': 'G. Wacokecoke',
                'J. Brex': 'N. Brex',
                'E. Hill': 'T. Hill',
                'O. Segun': 'R. Segun'
                }
    #TODO add in here lookup by initial and second name
    try:
        players = [[p.split(',,')[0], len(p.split(',,'))-1] for p in dict_lst[dict_key]]

        for p in players:
            #player name not recorded 
            if len(p[0])<=3:
                continue

            try:
                idx_p = name_lookup.index(p[0])
                df.loc[idx_p,[df_col]] = p[1]
            except:
                try:#try for miss spelling
                    idx_p = name_lookup.index(spelling[p[0]])
                    df.loc[idx_p,[df_col]] = p[1]
                except:
                    print('Cannot find player {0}'.format(p[0]))
    except:
        #if no penalty goals in game
        pass

def clean_df(df, list_ids, at_home, target_details, name_lookup):
    df['at_home'] = at_home

    #clean table
    cols_to_drop =[col for col in df.columns if 'Unnamed' in col]
    df = df.drop(cols_to_drop, axis=1)
    #rename column to player for player details
    df.columns.values[0] = 'player'
    #drop empty row in player df
    df = df[df['player'].notna()]

    #determine minutes played and subs and add to dataframe
    p_name, min_played, is_sub, pos_num = extract_sub_data(df['player'].values)
    df['name'] = p_name
    df['mins_played'] = min_played
    df['is_sub'] = is_sub
    df['position_num'] = pos_num 

    #remove replacements column
    df.drop([p_name.index('Replacements')], inplace=True)

    #add in player ids
    df['playguid'] = lookup_PlayGuid_list(df['name'].values, list_ids)

    #drop reformatted columns
    df.drop(['player'], axis=1, inplace=True)

    #rename columns for database
    df.columns = map(renaming_fun, df.columns)

    #add target detaild for penos, tries and convos
    dict_lst = create_dict_special(target_details, at_home)

    df['penalty_goals'] = 0
    add_target_values('Penalties',dict_lst, 'penalty_goals', df, name_lookup[at_home])

    df['tries'] = 0
    add_target_values('Tries',dict_lst, 'tries', df, name_lookup[at_home])
    #add_target_values('Penalty Tries',dict_lst, 'tries', df)

    df['conversions'] = 0
    add_target_values('Conversions',dict_lst, 'conversions', df, name_lookup[at_home])

    #remove players who did not play or we dont know for how long
    df = df[df['is_sub'] >= 0]

    #reset index
    df = df.reset_index(drop=True)
    return(df)

def load_to_db(comp ,year, loaded_dict):
    #connect to db
    db_tool = db_api()

    #legacy
    list_of_dfs = []

    #create compitition record
    table = 'Comps' 
    insert_dict = {'name': comp,
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
        if len(loaded_dict[i]['name_lookup'][0])==0:
            print('Game {} has no preview information so skiping upload to DB'.format(i))
            continue

        df1 = clean_df(loaded_dict[i]['home_df'], loaded_dict[i]['home_player_ids'],
                      1, loaded_dict[i]['target_details'], loaded_dict[i]['name_lookup'])

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
                       0, loaded_dict[i]['target_details'], loaded_dict[i]['name_lookup'])

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


### Champions Cup ###
pickle_path = os.getcwd() + '\\Scrapers\\Scraped Data\\champions_cup_matches.pkl'
with open(pickle_path, 'rb') as f:
    loaded_dict = pickle.load(f)

master_df = load_to_db('Champions Cup', 2022, loaded_dict)

save_path =  os.getcwd() + '\\Data Cleaners\\Cleaner_Data\\champions_cup_matches.csv'

master_df.to_csv(save_path)


### Challenge Cup ###
pickle_path = os.getcwd() + '\\Scrapers\\Scraped Data\\challenge_cup_matches.pkl'
with open(pickle_path, 'rb') as f:
    loaded_dict = pickle.load(f)

master_df = load_to_db('Challenge Cup', 2022, loaded_dict)

save_path =  os.getcwd() + '\\Data Cleaners\\Cleaner_Data\\challenge_cup_matches.csv'

master_df.to_csv(save_path)
