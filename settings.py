from sqlalchemy import create_engine
from database import MyBase
from os import getenv
from dotenv import load_dotenv


load_dotenv()


ENGINE = create_engine(getenv('DATABASE_URL'))
MyBase.metadata.create_all(ENGINE)
TWITTER_TOKEN = getenv('TWITTER_TOKEN')
