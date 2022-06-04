import pymysql
import os
import pickle
import base64
#### Create the schema ####

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
    )

c = conn.cursor()
sql = 'CREATE SCHEMA {0}'.format(conn_dict['dbname'])
c.execute(sql)
conn.close()
