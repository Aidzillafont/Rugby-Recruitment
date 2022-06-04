import base64
import os
import subprocess
import pickle

##### Password Creation and Encryption ####
val = input("Enter desired password: ")
confirm = input("Confirm desired password: ")

while  val != confirm:
    print('Passwords are different please try again.')
    val = input("Enter desired password: ")
    confirm = input("Confirm desired password: ")

encoded = base64.b64encode(val.encode("utf-8"))

save_path = os.getcwd() + '\\Database\\secret'

with open(save_path, 'wb') as f:
    f.write(encoded)

print('encoded password has been saved here {0}'.format(save_path), 'KEEP THIS A SECRET!!!', sep='\n')


##### Docker Creation and connection object #####
print('MAKE SURE YOU HAVE DOCKER OPEN!!!')

name = str(input("Enter desired DB name: "))
port = int(input("Enter desired DB port: "))

save_path =  os.getcwd() + '\\Database\\conn_pickle.pkl'

conn_dict = {'host':'localhost', 'dbname': name, 'user':'root', 'port':port}
with open(save_path, 'wb') as f:
    pickle.dump(conn_dict, f)
    print('Connection pickle file saved to', save_path, sep=': ')

print('Now the below docker command will run creating your DB:')
docker_creation  = 'docker run --name {0} -e MYSQL_ROOT_PASSWORD={1} -p {2}:3306 -d mysql:latest'.format(name,val, port)
print(docker_creation)
subprocess.call(docker_creation, shell=True)

