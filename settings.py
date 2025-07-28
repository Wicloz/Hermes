from sqlalchemy import create_engine
from database import MyBase
from os import environ


def load_dotenv():
    with open('.env', 'r') as fp:
        for line in fp:
            line = line.split('#', 1)[0]
            if '=' in line:
                key, value = line.split('=', 1)
                environ[key.strip()] = value.strip()


load_dotenv()
ENGINE = create_engine(environ.get('DATABASE_URL'))
MyBase.metadata.create_all(ENGINE)
TWITTER_TOKEN = environ.get('TWITTER_TOKEN')
