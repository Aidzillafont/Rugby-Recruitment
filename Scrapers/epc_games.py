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

def get_links_to_games(browser, year, comp, url):
    ###
    #year must be format yyyy0-yyyy1 ie 2021-2022
    ###
    ##### GAME LIST ######
    browser.get(url)

    #select year of tournament 
    css_selector_dropdown = '#mainSite > section > main > div > div > div > div > div.widget-dropdown.widget-dropdown-season.clearfix.no-filters > select'
    wait_by_selector(browser, css_selector_dropdown) 
    select = Select(browser.find_element_by_css_selector(css_selector_dropdown))
    select.select_by_visible_text(str(year))

    ##wait for selection to load
    #css_wait = '#sotic_wp_widget-183-content > div > div > div:nth-child(3) > div.fixtures__links.p-relative > span > a'
    #wait_by_selector(browser, css_wait)

    #load page to soup
    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')
    main_site = soup.find('section', {'class': 'mainSite-container'})
    games = main_site.find_all('a', {'class': 'matchLink'})

    #get links to games
    game_links = [a.get('href') for a in games]

    #add to dictionary and dataframe for saving to csv with pandas
    links_dict = {'game_links': game_links}
    df = pd.DataFrame(links_dict) 
    save_path =  os.getcwd() + '\\Scrapers\\Scraped Data\\game_links_{0}_{1}.csv'.format(comp,str(year))
    df.to_csv(save_path)
    print('Link file saved to', save_path, sep=': ')

    return(game_links)

def get_match_stats_from_link(browser, link):
    url_MASK = 'https://www.epcrugby.com{0}#report'
    url = url_MASK.format(link)
    browser.get(url)
    time.sleep(10)

    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')

    tables = soup.find_all('table', {'class': 'table'})

    #some pages are missing data
    if len(tables)==0:
        return('Link was empty {0}'.format(link))

    home_df = pd.read_html(str(tables[0]))[0]
    away_df = pd.read_html(str(tables[1]))[0]

    home_player_ids = [(' '.join(s.a.text.replace('\n','').strip(' ').split()), s.a.get('href')) for s in tables[0].find_all('span', {'class': 'pos-name'})]
    away_player_ids = [(' '.join(s.a.text.replace('\n','').strip(' ').split()), s.a.get('href')) for s in tables[1].find_all('span', {'class': 'pos-name'})]

    #Special requirement to get trys penos and conversions
    summary = soup.find('div', {'class': 'match-widget match-summary-widget'})
    header = soup.find_all('div',  {'class': 'matchEvent-header'})
    headers = [h.text.strip('\n') for h in header][:int(len(header)/2)]

    home_details = summary.find_all('div', {'class': 'teamAEvent'})
    home_details = [h.text.strip('\n').replace('\n\n\t','\n').replace('\n\n','|').replace('  ','').replace('\n',',').replace('\t','').split('|') for h in home_details]

    away_details = summary.find_all('div', {'class': 'teamBEvent'})
    away_details = [a.text.strip('\n').replace('\n\n\t','\n').replace('\n\n','|').replace('  ','').replace('\n',',').replace('\t','').split('|')  for a in away_details]

    target_details = [away_details, home_details, headers]

    #lookup for names
    home_names = [div.text.strip('\n').split('\n')[0] for div in soup.find_all('div', {'class': 'lineup-teamA-name'})]
    away_names = [div.text.strip('\n').split('\n')[0] for div in soup.find_all('div', {'class': 'lineup-teamB-name'})]

    name_lookup = [away_names, home_names]

    #home team
    css_home_team = '#sotic_wp_widget-83-content > div > div > div.matchPage-matchTeams > div.matchPage-matchNames > div.matchNames-teamA.teamName > span'
    home_team = soup.select_one(css_home_team)
    home_team = home_team.text.strip('\n').strip(' ').strip('\n')

    #away team
    css_away_team = '#sotic_wp_widget-83-content > div > div > div.matchPage-matchTeams > div.matchPage-matchNames > div.matchNames-teamB.teamName > span'
    away_team = soup.select_one(css_away_team)
    away_team = away_team.text.strip('\n').strip(' ').strip('\n')

    #FT Score
    css_FT_A = '#sotic_wp_widget-83-content > div > div > div.matchPage-matchScores > div.matchScore-main > div.matchScore-teamA > span'
    css_FT_B = '#sotic_wp_widget-83-content > div > div > div.matchPage-matchScores > div.matchScore-main > div.matchScore-teamB > span'
    FT_Score_A = soup.select_one(css_FT_A)
    FT_Score_A = FT_Score_A.text.strip('\n').strip(' ').strip('\n')
    FT_Score_B = soup.select_one(css_FT_B)
    FT_Score_B = FT_Score_B.text.strip('\n').strip(' ').strip('\n')
    FT_Score = FT_Score_A + ' - ' + FT_Score_B

    #HT Score
    css_HT = '#sotic_wp_widget-83-content > div > div > div.matchPage-matchMeta > div.matchPage-matchFinal.hidden-xs.hidden-sm > div > span'
    HT_Score = soup.select_one(css_HT)
    #some pages dont have half time score
    if HT_Score is not None:
        HT_Score = HT_Score.text.strip('\n').strip(' ').strip('\n').strip('HT ')
    else:
        HT_Score = 'Not Found'

    #Date
    css_date = '#sotic_wp_widget-83-content > div > div > div.matchPage-matchMeta > div.matchPage-MetaInner > div.matchMeta-top > span.matchDate'
    match_date = soup.select_one(css_date)
    match_date = match_date.text.strip('\n').strip(' ').strip('\n')

    match_key = ['home_team', 'away_team', 'FT_Score', 'HT_Score', 'match_date', 'home_df', 'away_df', 'home_player_ids', 'away_player_ids', 'target_details', 'name_lookup']
    match_value = [home_team, away_team, FT_Score, HT_Score, match_date, home_df, away_df, home_player_ids, away_player_ids, target_details, name_lookup]
    match_dict = dict(zip(match_key, match_value))

    return(match_dict)

def check_for_duplicates(master_dict):
#duplicates from scraping can only appear sequentially
    for i in range(1,len(master_dict)):
        if isinstance(master_dict[i], str):
            print(i, master_dict[i], sep=':  ')
            continue
        if isinstance(master_dict[i-1], str):
            continue

        if master_dict[i]['FT_Score']==master_dict[i-1]['FT_Score'] and master_dict[i]['home_team']==master_dict[i-1]['home_team']:
            print(i, 'Possible Dupe', sep=':  ')

from selenium import webdriver

webdriver_path = os.getcwd() + '\\Scrapers\\webdriver\\geckodriver.exe'
browser = webdriver.Firefox(executable_path=webdriver_path)

#len(main_site.find_all('a', {'class': 'matchLink'}))
#url = 'https://www.epcrugby.com/champions-cup/matches/fixtures-and-results/'
#game_links_HC = get_links_to_games(browser, '2021-2022', 'champions_cup', url)
#url = 'https://www.epcrugby.com/challenge-cup/matches/fixtures-and-results/'
#game_links_CC = get_links_to_games(browser, '2021-2022', 'challenge_cup', url)


#### HEINIKEN CHAMPIONS CUP ####
game_links_HC =  list(pd.read_csv(os.getcwd() + '\\Scrapers\\Scraped Data\\game_links_champions_cup_2021-2022.csv')['game_links'])

i = 0
master_dict = {}
##### GAME STATS BY PLAYER ######
for link in tqdm(game_links_HC):
    master_dict[i] = get_match_stats_from_link(browser, link)
    i+=1

check_for_duplicates(master_dict)

#write to a pickle file for reading later
save_path =  os.getcwd() + '\\Scrapers\\Scraped Data\\champions_cup_matches.pkl'
with open(save_path, 'wb') as f:
    pickle.dump(master_dict, f)
    print('Matches file saved to', save_path, sep=': ')
 

#### Challange CUP ####
game_links_HC =  list(pd.read_csv(os.getcwd() + '\\Scrapers\\Scraped Data\\game_links_challenge_cup_2021-2022.csv')['game_links'])

i = 0
master_dict = {}
##### GAME STATS BY PLAYER ######
for link in tqdm(game_links_HC):
    master_dict[i] = get_match_stats_from_link(browser, link)
    i+=1

check_for_duplicates(master_dict)

#write to a pickle file for reading later
save_path =  os.getcwd() + '\\Scrapers\\Scraped Data\\challenge_cup_matches.pkl'
with open(save_path, 'wb') as f:
    pickle.dump(master_dict, f)
    print('Matches file saved to', save_path, sep=': ')


browser.quit()


