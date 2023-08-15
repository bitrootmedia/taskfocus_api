# TaskFocus API 

REST api made with Django DRF for Task Management apps - TaskFocus. 
The goal is to make a simple but flexible project/task management app.


## Requirements 
Python 3.9+


## Local development setup
Run the following command to create the venv, taskfocus is the name of the venv. 

`python -m venv taskfocus`
`source venv/bin/activate` or `\venv\taskfocus\Scripts\activate.ps1` (Windows)

Navigate to your project, copied from github and run to install dependencies.

`pip install -r requirements.txt`


## .env file 
Copy .env.base to .env and replace the values where needed.


## setup Database and superuser

Run `./manage.py migrate` followed by `./manage.py createsuperuser` to create an admin account.


## Test

`./manage.py test`


## Run server

Finally, run `./manage.py runserver` to start your server. 
Keep the shell open and navigate to http://127.0.0.1:8000 in your browser to see the outcome.


## API Docs 

Schema is available at: 
`/api/schema` 

ReDoc:
`/api/schema/redoc/`

Swagger:
`/api/schema/swagger-ui/`


TODO: pre-commit, flake 