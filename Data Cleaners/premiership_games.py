import os
import pickle
import numpy as np
import pandas as pd
from tqdm import tqdm

pickle_path = os.getcwd() + '\\Scrapers\\Scraped Data\\premiership_matches.pkl'
with open(pickle_path, 'rb') as f:
    loaded_dict = pickle.load(f)


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
        if len(subs) == 1:
            #no subs
            p_name.append(subs[0])
            min_played.append(80)

            #issue where some subs do not have replacements data on site
            if sub_flag:
                is_sub.append(1)
                pos_num.append(-1)
                continue

            #TODO: once data set is clean see how many subs have 80m 
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

def clean_df(df, list_ids, at_home):
    df['at_home'] = at_home

    #determine minutes played and subs and add to dataframe
    p_name, min_played, is_sub, pos_num = extract_sub_data(df[['Pos','Player']].values)
    df['p_name'] = p_name
    df['min_played'] = min_played
    df['is_sub'] = is_sub
    df['pos_num'] = pos_num 

    #remove replacements column
    df.drop([p_name.index('Replacements')], inplace=True)

    #add in player ids
    df['PlayGuid'] = lookup_PlayGuid_list(df['p_name'].values, list_ids)

    #drop reformatted columns
    df.drop(['Pos', 'Player'], axis=1, inplace=True)

    df = df.replace('-',0)
    return(df)

list_of_dfs = []

for i in tqdm(range(0, 158)):
    if isinstance(loaded_dict[i], str):
        print(i, loaded_dict[i], sep=':  ')
        continue

    #get cleaned home and away data
    df1 = clean_df(loaded_dict[i]['home_df'], loaded_dict[i]['home_player_ids'], 1)
    list_of_dfs.append(df1)

    df2 = clean_df(loaded_dict[i]['away_df'], loaded_dict[i]['away_player_ids'], 0)
    list_of_dfs.append(df2)

master_df = pd.concat(list_of_dfs)

master_df.reset_index(inplace = True, drop=True)

save_path =  os.getcwd() + '\\Data Cleaners\\Cleaner_Data\\premiership_matches.csv'

master_df.to_csv(save_path)


counter = master_df['PlayGuid'].value_counts().to_frame()

counter[counter['PlayGuid']>10]
