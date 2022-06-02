import os
import pickle
import numpy as np
import pandas as pd
from tqdm import tqdm


pickle_path = os.getcwd() + '\\Scrapers\\Scraped Data\\sixnation_matches.pkl'
with open(pickle_path, 'rb') as f:
    loaded_dict = pickle.load(f)

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
    pos_num = df[df['Player']==off_rep].iloc[0]['pos_num']

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
    df['pos_num'] = [int(p.split('  ')[0]) for p in df['Player']]
    df['Player'] = [p.split('  ')[1] for p in df['Player']]
    df['is_sub'] = [1 if p>15 else 0 for p in df['pos_num']]
    df['pos_num_y'] = df[['Player','pos_num']].apply(lambda x: get_position_subsitution(x, on_reps, off_reps, df), axis=1)

    df['PlayGuid'] = get_PlayGuid(dict['{0}_player_ids'.format(team)])

    return(df)

check_for_duplicates(loaded_dict)


list_of_dfs = []

for i in tqdm(range(0,len(loaded_dict))):
    #home
    df1 = create_clean_df(loaded_dict[i], 1)
    list_of_dfs.append(df1)
    #away
    df2 = create_clean_df(loaded_dict[i], 0)
    list_of_dfs.append(df2)


master_df = pd.concat(list_of_dfs)
master_df.reset_index(inplace = True, drop=True)

save_path =  os.getcwd() + '\\Data Cleaners\\Cleaner_Data\\sixnations_matches.csv'

master_df.to_csv(save_path)


master_df.groupby('player').count()

master_df['Player'].value_counts()
master_df['PlayGuid'].value_counts()
len(master_df['Player'].value_counts())



#Cut off time played i.e less than 10 minutes not included
#Look into storage solutions better than csv/pkl
# for website scrapes pickle since data may change out of our control
# Those pickles then can be transformed and loaded into mySQL to facilitae joins and master stat tables
#Think about outcome target
#front end thoughts (dash board type)
#direction of project to companies. Opta 
#resample not a first course of action need a good reason
#try simple classifiers