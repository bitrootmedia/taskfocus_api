# TaskFocus API 

REST api made with Django DRF for Task Management apps - TaskFocus. 
The goal is to make a simple but flexible project/task management app.


## Requirements 
Python 3.9+

## Local development setup

`python -m venv venv`
`source venv/bin/activate`

TODO: how to use pre-commit etc 

## .env file 
Create .env file in root directory 

For development use this should be enough:
`
SECRET_KEY="testing"
DEBUG=True
`
(TODO - add .env sample)

## Test

`./manage.py test`


## API Docs 

Schema is available at: 
`/api/schema` 

ReDoc:
`/api/schema/redoc/`

Swagger:
`/api/schema/swagger-ui/`
