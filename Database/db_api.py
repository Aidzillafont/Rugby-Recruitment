import base64
import os
import pymysql
import pickle
from datetime import datetime as dt

#safe_path = os.getcwd() + '\\Database\\secret'
#with open(safe_path, 'rb') as f:
#    encoded = f.read()
  
#pickle_path = os.getcwd() + '\\Database\\conn_pickle.pkl'
#with open(pickle_path, 'rb') as f:
#    conn_dict = pickle.load(f)

#conn = pymysql.connect(
#            host=conn_dict['host'],
#            user=conn_dict['user'], 
#            password = base64.b64decode(encoded.decode("utf-8")),
#            port=conn_dict['port'],
#            db=conn_dict['dbname'],
#            )

#TODO: 
# 1. Create loaders for six_nation and premiureship files
# 2. create downloader to get data from player matches

class db_api():
    def __init__(self):
        safe_path = os.getcwd() + '\\Database\\secret'
        pickle_path = os.getcwd() + '\\Database\\conn_pickle.pkl'

        with open(safe_path, 'rb') as f:
            encoded = f.read()
        with open(pickle_path, 'rb') as f:
            conn_dict = pickle.load(f)

        self.conn = pymysql.connect(
            host=conn_dict['host'],
            user=conn_dict['user'], 
            password = base64.b64decode(encoded.decode("utf-8")),
            port=conn_dict['port'],
            db=conn_dict['dbname'],
            )

    ### Genral Find Function ###
    def find(self, table, *return_vals, **where_kwargs): # date, home, away):
        col_str = ', '.join(*return_vals)
        bool_str = ' AND '.join([str(key)+'=%s' for key in where_kwargs.keys()])
        params = [value for value in where_kwargs.values()]

        c = self.conn.cursor(pymysql.cursors.DictCursor)
        sql = 'Select {0} from {1} where {2}'.format(col_str, table, bool_str)
        c.execute(sql, params)
        return c.fetchall()

    ### General Insert Function ###
    def insert(self, table, **insert_kwargs): #idComp, date, home, away, FT_Score, HT_Score): 
        #check if exists to avoid duplicates
        is_empty = self.find(table, ['*'], **insert_kwargs)==()
        if not is_empty:
            return self.find(table, ['*'], **insert_kwargs)


        insert_str = ', '.join([str(key) for key in insert_kwargs.keys()])
        s_str = ', '.join(['%s' for key in insert_kwargs.keys()])
        params = [value for value in insert_kwargs.values()]

        c = self.conn.cursor()
        sql = 'INSERT INTO {0} ({1}) VALUES ({2})'.format(table, insert_str, s_str)
        c.execute(sql, params)
        self.conn.commit()

        return self.find(table, ['*'], **insert_kwargs)


#db_tool = db_api()


##how to use insert
### Insert Players first
#table = 'Players' 
#insert_dict = {'playguid':'ABC123',
#               'name': 'Jack Ball'}
#player = db_tool.insert(table, **insert_dict)

### Insert Comp Next 
#table = 'Comps' 
#insert_dict = {'name': 'WorldKup',
#               'year': 2022}
#comp = db_tool.insert(table, **insert_dict)

### Insert Matches Next 
#table = 'Matches' 
#insert_dict = {'idComp':comp[0]['idComp'],
#               'date': dt(2019, 12, 4),
#               'home': 'Hells Angels',
#               'away': 'Hevans Devils',
#               'FT_Score': '22-13',
#               'HT_Score': '5-7'
#               }
#match = db_tool.insert(table, **insert_dict)

### Insert Player_Matches finally 
#table = 'Player_Matches'
#insert_dict = {  
#  'idPlayer': player[0]['idPlayer'] ,
#  'idMatch': match[0]['idMatch'] , 
#  'position_num': 15,
#  'mins_played': 46,
#  'tries': 2,
#  'try_assists': 2,
#  'conversions': 2,
#  'penalty_goals': 2,
#  'drop_goals': 2,
#  'meters_made': 2,
#  'carries': 2,
#  'possession_kicked_pct': 2,
#  'meters_kicked': 2,
#  'balls_played_by_hand': 2,
#  'passes_made': 2,
#  'offloads': 2,
#  'broken_tackles': 2,
#  'knock_ons': 2,
#  'tackles_made': 2,
#  'missed_tackles': 2,
#  'tackle_success_pct': 100.00,
#  'dominant_tackles_pct': 2,
#  'turnovers_won': 2,
#  'turnovers_conceded': 2,
#  'handling_errors': 2,
#  'pens_conceded': 2,
#  'offside_penalties': 2,
#  'scrum_penalties': 2,
#  'lineouts_won': 2,
#  'lineouts_stolen': 2,
#  'defemders_beaten': 2,
#  'clean_breaks': 2,
#  'at_home': 1,
#  'is_sub': 1}

#db_tool.insert(table, **insert_dict)


##how to use find
#table = 'Matches'
#return_vals = ['idMatch', 'idComp', 'date', 'FT_Score']
#where_dict = {'date': dt(2019, 12, 4),
#               'home': 'Hells Angels',
#               'away': 'Hevans Devils',
#               }

#db_tool.find(table, return_vals, **where_dict)
