PRE-REQUSITS
Docker with MySQL
Python

INSTALLATION
To set up database run the following python scripts in order and follow instructions on screen

1. Run db_init_script.py
	this creates the docker container and will create a secret and connection file with encrypted password and connection details

2. Run db_create_schema.py
	this will connect using created files to your docker mysql instance and create a schema

3. Run db_rn_config.py
	this this will run in configuration scripts to create tables