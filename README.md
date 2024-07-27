# PhotoShare FastAPI
### Table of Contents
- [Introduction](#introduction)
  - [Links to test instance and documentation](#links-to-test-instance-and-documentation)
  - [Technologies](#)
- [Some features](#features)
- [Installation and launch](#)
  - [Prerequisites](#)
  - [Install and run locally](#)
  - [Install and run on server](#)
- [License](#license)
- [Contributing](#contributing)
- [Contact](#contact)

## Introduction
PhotoShare FastAPI is a comprehensive REST API application that facilitates user photo sharing. It provides robust functionality for managing and cloud store images. Users can add descriptions, tags and comments to shared photos. The application is also providing secure user authentication.

I have created the project as a solution to the final assignment for one of the stages of the `Python Developer` course organized by [GoIT Polska](https://www.goit.global/pl).

### Links to test instance and documentation
> [!CAUTION]
> This is a test instance, which can be turned off or moved to another address at any time, and all data can be deleted. Don't give any true personal information there, or post relevant and/or private photos or images. Current addresses of the test instance and documentation will be published here.
#### Here you can test the app in action (using [Swagger](https://swagger.io/) or [ReDoc](https://redocly.github.io/redoc/)):
* [PhotoShare-fastapi-Swagger](https://divine-shaun-goit-project-3160ff2e.koyeb.app/docs#/)
* [PhotoShare-fastapi-ReDoc](https://divine-shaun-goit-project-3160ff2e.koyeb.app/redoc)

#### Here you can see the documentation  (created using [Sphinx](https://www.sphinx-doc.org/en/master/)):
* [PhotoShare-fastapi-doc](https://photoshare-fastapi-docs.tiiny.site/)


### Some of the technologies used to create the app:
- [Python](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/en/latest/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)
- [Uvicorn](https://www.uvicorn.org/)
- [Docker](https://www.docker.com/)
- [Poetry](https://python-poetry.org/)
- [bcrypt](https://pypi.org/project/bcrypt/)
- [Sphinx](https://www.sphinx-doc.org/en/master/)
- [qrcode](https://pypi.org/project/qrcode/)
- [Cloudinary](https://cloudinary.com/)
- [pytest](https://docs.pytest.org/en/latest/)

## Some features:
- Authentication of users using JWT tokens with the ability to log in from multiple devices.
- Assigning roles to users (admin, moderator, standard), with admin only able to be added via script: ```python manage.py create_admin```.
- Admins can change the role of other users (from standard to moderator or vice versa).
- Upload, delete, and edit photos with descriptions and up to five tags.
- Transformations for photos (crop, resize, rotate, grayscale, blur, add special effects and much more).
- Links for retrieving uploaded photos and their transformations.
- Qrcode generation for photos and its transformations.
- Search photos by tags and descriptions.
- Ability to comment on photos along with the ability to edit comments.
- Moderators and administrators can delete comments.
- User profiles with editable information.
- Moderators and administrators can deactivate/activate users (moderators only standard or moderator users). 
- Administrator can delete users.

## Installation and launch
### Prerequisites:
- Python 3.11 or higher
- Cloudinary account (you can create one for free on [Cloudinary](https://cloudinary.com/))
- Git (optional but recommended)
- Docker (optional but recommended f.e. for launch PostgreSQL and Redis locally in containers)
- PostgreSQL database
- Redis instance
- Poetry (optional)
### Install and run locally:

1. Clone the repository to the folder of your choice:
```
git clone https://github.com/Szumapman/PhotoShare_fastapi.git
```
or download the project as a zip archive and unzip it.
Then go to the project directory:
```
cd PhotoShare_fastapi
```
2. Create a virtual environment and install the dependencies:
Using Poetry:
start the virtual environment:
```
poetry shell
```
install dependencies:
```
poetry install
```
or you can install all dependencies (including test and dev) with:
```
poetry install --with test,dev
```
Alternatively, you can use pip:
start the virtual environment and activate it (optional but recommended):
(depending on your OS you may need to slightly change the command f.e. change python to python3 or properly activate virtual
environment):
```
python -m venv venv
source venv/bin/activate
```
install dependencies:
```
pip install -r requirements.txt
```
you can also install dependencies for test and dev with:
```
pip install -r requirements-test.txt
```
```
pip install -r requirements-dev.txt
```
3. Create an .env file in the project root and add the following variables:
```
POSTGRES_DB=<POSTGRES_DB_NAME>
POSTGRES_USER=<POSTGRES_USER_NAME>
POSTGRES_PASSWORD=<POSTGRES_PASSWORD>
POSTGRES_HOST=<POSTGRES_HOST>
POSTGRES_PORT=<POSTGRES_PORT>

SQLALCHEMY_DATABASE_URL=<SQLALCHEMY_DATABASE_URL>

SECRET_KEY=<SECRET_KEY>
ALGORITHM=<ALGORITHM>

REDIS_HOST=<REDIS_HOST>
REDIS_PORT=<REDIS_PORT>
REDIS_PASSWORD=<REDIS_PASSWORD>

CLOUDINARY_NAME=<CLOUDINARY_USER_NAME>
CLOUDINARY_API_KEY=<CLOUDINARY_API_KEY>
CLOUDINARY_API_SECRET=<CLOUDINARY_API_SECRET>
```
You can copy the [env.example](env.example) file rename it to .env and change the variables to your own. 

Here is an example of the.env file to use with PostgreSQL and Redis running in containers (you have to add yours cloudinary credentials and you should at least
change the secret key and passwords):
```
# PostgreSQL 
POSTGRES_DB=photoshare_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# JWT encryption
SECRET_KEY=your_secret_key
ALGORITHM=HS256

# Redis 
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Cloudinary
CLOUDINARY_NAME={your_cloudinary_name}
CLOUDINARY_API_KEY={your_cloudinary_api_key}
CLOUDINARY_API_SECRET={your_cloudinary_api_secret}
```
4. Start the database and Redis instances:
if you are using docker, first make sure that it runs, then:
```
docker compose up -d
```
or make sure that your instances of PostgreSQL and Redis are running.
5. Create the database tables by applying the migrations:
```
alembic upgrade head
```
6. Launch the application:
```
python main.py
```
or by explicitly running the `uvicorn` server:
```
uvicorn main:app --host localhost --port 8000 --reload
```

7. Open the application in the browser:
```
http://localhost:8000/docs
```
or
```
http://localhost:8000/redoc
```
### Install and run on server:
1. Do the 1-2 steps from the previous section.
2. Create an .env file in the project root and add the following variables:
```
POSTGRES_DB=<POSTGRES_DB_NAME>
POSTGRES_USER=<POSTGRES_USER_NAME>
POSTGRES_PASSWORD=<POSTGRES_PASSWORD>
POSTGRES_HOST=<POSTGRES_HOST>
POSTGRES_PORT=<POSTGRES_PORT>

SQLALCHEMY_DATABASE_URL=<SQLALCHEMY_DATABASE_URL>

SECRET_KEY=<SECRET_KEY>
ALGORITHM=<ALGORITHM>

REDIS_HOST=<REDIS_HOST>
REDIS_PORT=<REDIS_PORT>
REDIS_PASSWORD=<REDIS_PASSWORD>

CLOUDINARY_NAME=<CLOUDINARY_USER_NAME>
CLOUDINARY_API_KEY=<CLOUDINARY_API_KEY>
CLOUDINARY_API_SECRET=<CLOUDINARY_API_SECRET>
```
You will need the database and Redis instances running on the servers of your choice.
3. Create the database tables by applying the migrations:
```
alembic upgrade head
```
4. Create docker image (optional but recommended), the dockerfile is in the project root:
```
docker build -t your_image_name .
```
5. Deploy the app to the server, I'm recommending using the docker image created in the previous step.


## License
This application is provided under the [MIT license](https://github.com/Szumapman/PhotoShare_fastapi?tab=MIT-1-ov-file#)

## Contributing

If you would like to contribute to the project, please feel free to fork the repository and make a pull request.

## Contact
#### Project created by [Paweł Szumański](https://github.com/Szumapman)

If you have any questions, or suggestions or want to get in touch about the application, please [email me](mailto:pawel.szumanski@outlook.com).
