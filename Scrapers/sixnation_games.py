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
    ##### GAME LIST ######
    url = 'https://www.sixnationsrugby.com/fixtures/'
    browser.get(url)

    #select year of tournament 
    css_selector_dropdown = '#fixture-controls > div.fixtures__filters-block > div.fixtures__filters-season > select'
    wait_by_selector(browser, css_selector_dropdown) 
    select = Select(browser.find_element_by_css_selector(css_selector_dropdown))
    select.select_by_visible_text(str(year))

    #wait for selection to load
    css_selector_first_link = '#fixture-list > div > div > div:nth-child(1) > div:nth-child(2) > span > a'
    wait_by_selector(browser, css_selector_first_link)

    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')
    games = soup.find_all('span', {'class': 'outer__link'})
    #get links to games
    game_links = [span.a.get('href') for span in games]

    #add to dictionary and dataframe for saving to csv with pandas
    links_dict = {'game_links': game_links}
    df = pd.DataFrame(links_dict) 
    save_path =  os.getcwd() + '\\Scrapers\\Scraped Data\\game_links_sixnations_{0}.csv'.format(str(year))
    df.to_csv(save_path)
    print('Link file saved to', save_path, sep=': ')

    return(game_links)

def get_match_stats_from_link(browser, link):
    url_MASK = 'https://www.sixnationsrugby.com/{0}#match-stats'
    url = url_MASK.format(link)
    
    browser.get(url)

    #initialization wait since web page can take a while to load
    time.sleep(30)

    #wait for player table to load
    css_selector_player_stats = '#player-stats > div > div.match-content__playerstats.player-stats.match-centre__player-table-wrapper'
    wait_by_selector(browser, css_selector_player_stats)

    #player tab selector click to
    css_player_tab = '#content > div.match__content.row > div.content-match-stats.data-tab.tab-content-active > div.ta-centre > div > span:nth-child(2)'
    browser.find_element_by_css_selector(css_player_tab).click()

    #table selector
    css_table_selector = "#player-stats > div > div.match-content__playerstats.player-stats.match-centre__player-table-wrapper > div.data-tab.tab-content-active > table"
    wait_by_selector(browser, css_table_selector)

    #get html team 1
    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.select_one(css_table_selector)
    home_df = pd.read_html(str(table))[0]
    home_player_ids = [(p.a.text.strip('\n').strip(' ').strip('\n'), p.a.get('href')) for p in table.find_all('td', {'class': 'player-report'})]

    #click to get second team
    css_selector_to_click = '#player-stats > div > div.match-navigation__playerstats.ta-left.mt-1 > span:nth-child(2)'
    wait_by_selector(browser, css_selector_to_click)
    browser.find_element_by_css_selector(css_selector_to_click).click()
    wait_by_selector(browser, css_table_selector)

    #get html team 2
    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.select_one(css_table_selector)
    away_df = pd.read_html(str(table))[0]
    away_player_ids = [(p.a.text.strip('\n').strip(' ').strip('\n'), p.a.get('href')) for p in table.find_all('td', {'class': 'player-report'})]

    #home team
    css_home_team = '#fix-info > div > div > div.fixture-info__inner > div.fixture-info__team-info > div.fixture-info__teama > span'
    home_team = soup.select_one(css_home_team)
    home_team = home_team.text.strip('\n').strip(' ').strip('\n')

    #away team
    css_away_team = '#fix-info > div > div > div.fixture-info__inner > div.fixture-info__team-info > div.fixture-info__teamb > span'
    away_team = soup.select_one(css_away_team)
    away_team = away_team.text.strip('\n').strip(' ').strip('\n')

    #FT Score
    css_FT = '#fix-info > div > div > div.fixture-info__inner > div.fixture-info__team-info > div.fixture-info__details > div > span.fixture-info__ft.tf-heading.d-block'
    FT_Score = soup.select_one(css_FT)
    FT_Score = FT_Score.text.strip('\n').strip(' ').strip('\n')

    #HT Score
    css_HT = '#fix-info > div > div > div.fixture-info__inner > div.fixture-info__team-info > div.fixture-info__details > div > span.fixture-info__ht.d-block.tf-heading'
    HT_Score = soup.select_one(css_HT)
    HT_Score = HT_Score.text.strip('\n').strip(' ').strip('\n').strip('HT: ')

    #Date
    css_date = '#fix-info > div > div > div.fixture-info__inner > div.fixture-info__date-container > span'
    match_date = soup.select_one(css_date)
    match_date = match_date.text.strip('\n').strip(' ').strip('\n')

    #click live to get replacement data
    css_live_selector = '#content > div.match-centre__navigation > div > span:nth-child(3)'
    browser.find_element_by_css_selector(css_live_selector).click()
    #give a few seconds to load
    time.sleep(3)
    #wait for table
    css_timeline = '#timeline > div'
    wait_by_selector(browser, css_timeline)
    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')
    replacements = [r.text for r in soup.find_all('div', {'class': 'timeline__replacement timeline__player'})]

    match_key = ['home_team', 'away_team', 'FT_Score', 'HT_Score', 'match_date', 'home_df', 'away_df', 'home_player_ids', 'away_player_ids', 'replacements']
    match_value = [home_team, away_team, FT_Score, HT_Score, match_date, home_df, away_df, home_player_ids, away_player_ids, replacements]
    match_dict = dict(zip(match_key, match_value))

    return(match_dict)
    

from selenium import webdriver

webdriver_path = os.getcwd() + '\\Scrapers\\webdriver\\geckodriver.exe'
browser = webdriver.Firefox(executable_path=webdriver_path)

#game_links = get_links_to_games(browser, 2022)
game_links = list(pd.read_csv(os.getcwd() + '\\Scrapers\\Scraped Data\\game_links_sixnations_2022.csv')['game_links'])

i = 0
master_dict = {}
##### GAME STATS BY PLAYER ######
for link in game_links:
    master_dict[i] = get_match_stats_from_link(browser, link)
    i+=1


#write to a pickle file for reading later
save_path =  os.getcwd() + '\\Scrapers\\Scraped Data\\sixnation_matches.pkl'
with open(save_path, 'wb') as f:
    pickle.dump(master_dict, f)
    print('Matches file saved to', save_path, sep=': ')
    
browser.quit()

for i in range(1,15):
    print(master_dict[i]['FT_Score']==master_dict[i-1]['FT_Score'])




#from selenium import webdriver

#webdriver_path = os.getcwd() + '\\Scrapers\\webdriver\\geckodriver.exe'
#browser = webdriver.Firefox(executable_path=webdriver_path)
#url = 'https://www.sixnationsrugby.com/report/conway-at-the-double-as-ireland-defeat-wales-in-dublin#match-stats'
#browser.get(url)
##time.sleep(60)
#css_live_selector = '#content > div.match-centre__navigation > div > span:nth-child(3)'
#browser.find_element_by_css_selector(css_live_selector).click()
##time.sleep(5)
#html = browser.page_source
#soup = BeautifulSoup(html, 'html.parser')




#browser.quit()