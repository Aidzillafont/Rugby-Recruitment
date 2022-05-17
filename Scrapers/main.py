from premiership import get_player_links_premiership, get_player_dict_from_links_premiership
from selenium import webdriver
import os

webdriver_path = os.getcwd() + '\\Scrapers\\webdriver\\geckodriver.exe'
browser=webdriver.Firefox(executable_path=webdriver_path)
clubs = ['bath-rugby', 'bristol-bears', 'exeter-chiefs', 'gloucester-rugby', 'harlequins', 'leicester-tigers', 'london-irish',
         'newcastle-falcons', 'northampton-saints', 'sale-sharks', 'saracens', 'wasps', 'worcester-warriors']
links = get_player_links_premiership(browser, clubs)
data_dict = get_player_dict_from_links_premiership(browser,links)
browser.quit()