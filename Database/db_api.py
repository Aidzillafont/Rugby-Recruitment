import base64
import os
import pymysql
import pickle

safe_path = os.getcwd() + '\\Database\\secret'
with open(safe_path, 'rb') as f:
    encoded = f.read()
  
pickle_path = os.getcwd() + '\\Database\\conn_pickle.pkl'
with open(pickle_path, 'rb') as f:
    conn_dict = pickle.load(f)

print(base64.b64decode(encoded.decode("utf-8")))
conn_dict

conn = pymysql.connect(
            host=conn_dict['host'],
            user=conn_dict['user'], 
            password = base64.b64decode(encoded.decode("utf-8")),
            port=conn_dict['port'],
            db=conn_dict['dbname'],
            )

#TODO: 
# 1. Create loaders for six_nation and premiureship files
# 2. create downloader to get data from player matches

def create_match():
    pass