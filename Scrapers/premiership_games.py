from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import pickle
from tqdm import tqdm
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


#### A WAITING FUNCTION ####
def wait_by_selector(browser, css_selector):
    try:
        element = WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
        )
    finally:
        return 0


def get_links_to_games(browser, year):
    ###
    #year must be format yyyy0-yyyy1 ie 2021-2022
    ###
    ##### GAME LIST ######
    url = 'https://www.premiershiprugby.com/gallagher-premiership-rugby/fixtures-results/'
    browser.get(url)

    #select year of tournament 
    css_selector_dropdown = 'body > main > div.max__body-width > div > div.fixtures__options > div.fixtures__year > select'
    wait_by_selector(browser, css_selector_dropdown) 
    select = Select(browser.find_element_by_css_selector(css_selector_dropdown))
    select.select_by_visible_text(str(year))

    #wait for selection to load
    css_wait = '#sotic_wp_widget-183-content > div > div > div:nth-child(3) > div.fixtures__links.p-relative > span > a'
    wait_by_selector(browser, css_wait)

    #load page to soup
    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')
    games = soup.find_all('span', {'class': 'fixtures__link fixtures__link--match'})

    #get links to games
    game_links = [span.a.get('href') for span in games]

    #add to dictionary and dataframe for saving to csv with pandas
    links_dict = {'game_links': game_links}
    df = pd.DataFrame(links_dict) 
    save_path =  os.getcwd() + '\\Scrapers\\Scraped Data\\game_links_premiership_{0}.csv'.format(str(year))
    df.to_csv(save_path)
    print('Link file saved to', save_path, sep=': ')

    return(game_links)


def get_match_stats_from_link(browser, link):
    #some links are blank
    if len(link) == 2:
        return('Link was blank {0}'.format(link))

    url_MASK = 'https://www.premiershiprugby.com{0}#statistics'
    url = url_MASK.format(link)

    #some matches have not happended and some matches are missing

    #get and wait to load
    browser.get(url)
    time.sleep(10)

    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')

    tables = soup.find_all('table', {'class': 'table'})

    #some pages are missing data
    if len(tables)==0:
        return('Link was empty {0}'.format(link))

    #some matches have not happened yet
    if len(tables)==1:
        return('Match is yet to happen {0}'.format(link))

    #home is table at index 1 and away is table at index 2
    home_df = pd.read_html(str(tables[1]))[0]
    away_df = pd.read_html(str(tables[2]))[0]

    #get player names and ids links
    home_player_ids = [(' '.join(player.p.a.text.replace('\n','').strip(' ').split()), player.p.a.get('href')) for player in soup.find_all('div', {'class': 'team__player team__player-a ta-right'})]
    away_player_ids = [(' '.join(player.p.a.text.replace('\n','').strip(' ').split()), player.p.a.get('href')) for player in soup.find_all('div', {'class': 'team__player team__player-b'})]


    #home team
    css_home_team = '#sotic_wp_widget-197-content > div > div > div.match-performance__nav.p-1.ta-centre > span.tab.tab-nav-active'
    home_team = soup.select_one(css_home_team)
    home_team = home_team.text.strip('\n').strip(' ').strip('\n')

    #away team
    css_away_team = '#sotic_wp_widget-197-content > div > div > div.match-performance__nav.p-1.ta-centre > span:nth-child(2)'
    away_team = soup.select_one(css_away_team)
    away_team = away_team.text.strip('\n').strip(' ').strip('\n')

    #FT Score
    css_FT = '#sotic_wp_widget-211-content > div > div.match__scoreboard-main.ta-centre.pt-0-5.pb-1 > div > div.match__score.c-white.py-0-3.bg-primary > p'
    FT_Score = soup.select_one(css_FT)
    FT_Score = FT_Score.text.strip('\n').strip(' ').strip('\n')

    #HT Score
    css_HT = '#sotic_wp_widget-211-content > div > div.match__scoreboard-main.ta-centre.pt-0-5.pb-1 > div > div.match__score.c-white.py-0-3.bg-primary > small'
    HT_Score = soup.select_one(css_HT)
    HT_Score = HT_Score.text.strip('\n').strip(' ').strip('\n').strip('HT: ')

    #Date
    css_date = '#sotic_wp_widget-211-content > div > div.match__scoreboard-meta.ts-0-75.ta-centre.tf-allcaps.c-black.pt-1.pb-0-5.px-1.d-flex > div.match__meta-info.match__scoreboard-date.mr-0-8.c-black.d-inline-block'
    match_date = soup.select_one(css_date)
    match_date = match_date.text.strip('\n').strip(' ').strip('\n')

    match_key = ['home_team', 'away_team', 'FT_Score', 'HT_Score', 'match_date', 'home_df', 'away_df', 'home_player_ids', 'away_player_ids']
    match_value = [home_team, away_team, FT_Score, HT_Score, match_date, home_df, away_df, home_player_ids, away_player_ids]
    match_dict = dict(zip(match_key, match_value))

    return(match_dict)

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
    

from selenium import webdriver

webdriver_path = os.getcwd() + '\\Scrapers\\webdriver\\geckodriver.exe'
browser = webdriver.Firefox(executable_path=webdriver_path)

#game_links = get_links_to_games(browser, '2021-2022')
game_links =  list(pd.read_csv(os.getcwd() + '\\Scrapers\\Scraped Data\\game_links_premiership_2021-2022.csv')['game_links'])

i = 0
master_dict = {}
##### GAME STATS BY PLAYER ######
for link in tqdm(game_links):
    master_dict[i] = get_match_stats_from_link(browser, link)
    i+=1

check_for_duplicates(master_dict)

#write to a pickle file for reading later
save_path =  os.getcwd() + '\\Scrapers\\Scraped Data\\premiership_matches.pkl'
with open(save_path, 'wb') as f:
    pickle.dump(master_dict, f)
    print('Matches file saved to', save_path, sep=': ')
    
browser.quit()



