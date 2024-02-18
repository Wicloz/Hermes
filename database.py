from sqlalchemy import ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import List


class MyBase(DeclarativeBase):
    pass


class Link(MyBase):
    __tablename__ = 'links'
    id: Mapped[int] = mapped_column(primary_key=True)

    twitter_username: Mapped[str] = mapped_column()
    discord_channel: Mapped[int] = mapped_column()

    tasks: Mapped[List['Tasks']] = relationship(back_populates='link')

    __table_args__ = (
        UniqueConstraint('twitter_username', 'discord_channel'),
    )


class Tweet(MyBase):
    __tablename__ = 'tweets'
    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column()
    snowflake: Mapped[int] = mapped_column()
    type: Mapped[str] = mapped_column(Enum('tweet', 'retweet', name='tweet_types'))

    tasks: Mapped[List['Tasks']] = relationship(back_populates='tweet')

    __table_args__ = (
        UniqueConstraint('username', 'timestamp'),
        Index('idx_tweets_lookup', 'username', 'timestamp'),
    )


class Tasks(MyBase):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(primary_key=True)

    link_id: Mapped[int] = mapped_column(ForeignKey('links.id'))
    tweet_id: Mapped[int] = mapped_column(ForeignKey('tweets.id'))
    sent: Mapped[bool] = mapped_column(default=False)

    link: Mapped['Link'] = relationship(back_populates='tasks')
    tweet: Mapped['Tweet'] = relationship(back_populates='tasks')

    __table_args__ = (
        UniqueConstraint('link_id', 'tweet_id'),
    )
