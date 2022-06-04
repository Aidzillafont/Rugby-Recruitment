import pymysql
import os
import pickle
import base64
#### Create the schema ####

CONFIG_DIR = os.getcwd() + '\\Database\\DB_Creation\\SQL_Config_Scripts'

safe_path = os.getcwd() + '\\Database\\secret'
with open(safe_path, 'rb') as f:
    encoded = f.read()
  
pickle_path = os.getcwd() + '\\Database\\conn_pickle.pkl'
with open(pickle_path, 'rb') as f:
    conn_dict = pickle.load(f)

#Create the schema
conn = pymysql.connect(
    host=conn_dict['host'],
    user=conn_dict['user'], 
    password = base64.b64decode(encoded.decode("utf-8")),
    port=conn_dict['port'],
    db=conn_dict['dbname']
    )


for filename in os.listdir(CONFIG_DIR):
    config_file = os.path.join(CONFIG_DIR, filename)
    # checking if it is a file
    if os.path.isfile(config_file):
        with open(config_file, 'r') as f:
            with conn.cursor() as cursor:
                for sql in f.read().split(';')[:-1]:
                    cursor.execute(sql)
                    conn.commit()
