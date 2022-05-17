from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import pickle
from tqdm import tqdm

#a function to get player links
def get_player_links_premiership(browser, clubs):
    player_links = []
    url_club_MASK = 'https://www.premiershiprugby.com/club/{0}/#squad'
    for club in tqdm(clubs):
        browser.get(url_club_MASK.format(club))
        #allow page time to load
        time.sleep(5)
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        #find links as defined on website
        players = soup.find_all('a', {'class': 'p-absolute'})
        p_links = [p.get('href') for p in players]
        player_links.extend(p_links)
    
    #remove non player links captured
    player_links_clean = [p for p in player_links if 'PlayGuid' in p]
    
    #add to dictionary and dataframe for saving to csv with pandas
    links_dict = {'player_links': player_links_clean}
    df = pd.DataFrame(links_dict) 
    save_path =  os.getcwd() + '\\Scrapers\\Scraped Data\\player_links.csv'
    df.to_csv(save_path)
    print('Link file saved to', save_path, sep=': ')
    return(player_links_clean)

# a function to get player info from links
def get_player_dict_from_links_premiership(browser, links):
    #create a master dictionary
    master_dict = {}

    for link in tqdm(links):
        url_domain_MASK = 'https://www.premiershiprugby.com{0}'
        browser.get(url_domain_MASK.format(link))
        time.sleep(5)
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')

        stat_block = soup.find('div', {'class': 'player__statistic-block'})

        #skip player as no season statstics available
        if stat_block is None:
            continue
        if stat_block('p')[0].getText() == 'This player has no statistics available':
            continue

        #strip player guid as our key for master dictionary
        PlayGuid = re.search('PlayGuid=(.+?)&', link).group(1)

        #get profile info name, height, age, weight etc...
        name = soup.find('div', {'class': 'player__name px-1 pb-1'}).text.strip('\n')
        profile = soup.find('div', {'class': 'player__profile p-1 bg-white'})
        profile_key = [l.text for l in profile('h2')]
        profile_value = [v.text for v in profile('span')]
        profile_key.append('Name')
        profile_value.append(name)
        profile_dict = dict(zip(profile_key, profile_value))

        #get all season stats blocks
        stat_blocks = soup.find_all('div', {'class': 'player__statistic-block'})
        stats_list = []
        for b in stat_blocks:
            stat = [p.text for p in b.find_all('p')]
            stats_list.extend(stat)

        stats_key = stats_list[0::2]
        stats_value = stats_list[1::2]
        stats_dict = dict(zip(stats_key, stats_value))

        #get compition table
        table = soup.find('table', {'class': 'player__table player__table--career table table--striped'})
        comp_df = pd.read_html(str(table))[0]

        #create dict for player
        player_key = ['profile_dict', 'stat_dict', 'comp_df']
        player_value = [profile_dict, stats_dict, comp_df]
        player_dict = dict(zip(player_key, player_value))

        #add player to master dictionary
        master_dict[PlayGuid] = player_dict

    #write to a pickle file for reading later
    save_path =  os.getcwd() + '\\Scrapers\\Scraped Data\\premiership_dict.pkl'
    with open(save_path, 'wb') as f:
        pickle.dump(master_dict, f)
        
    print('Player Stats file saved to', save_path, sep=': ')
    return(master_dict)
