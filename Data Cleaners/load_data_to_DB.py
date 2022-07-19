import subprocess
import os


scripts = ['premiership_games_cleaner.py',
           'sixnations_games_cleaner.py',
           'epc_games_cleaner.py',
           'generate_profiles.py',
           'generate_team_match_stats.py'] 

for s in scripts:
    subprocess.call(['python', os.getcwd()+'\\Data Cleaners\\'+s])
    print("Finished:" + s)

