from sqlalchemy import ForeignKey, Enum, UniqueConstraint, Index, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional
import enum


class TweetMode(enum.Enum):
    TWEET = 'TWEET'
    RETWEET = 'RETWEET'


class WebhookMode(enum.Enum):
    DISCORD = 'DISCORD'
    ROCKETCHAT = 'ROCKETCHAT'


class MyBase(DeclarativeBase):
    pass


class Link(MyBase):
    __tablename__ = 'links'
    id: Mapped[int] = mapped_column(primary_key=True)

    twitter_username: Mapped[str] = mapped_column()
    webhook_type: Mapped[WebhookMode] = mapped_column(Enum(WebhookMode))
    webhook_url: Mapped[str] = mapped_column()
    webhook_pings: Mapped[Optional[str]] = mapped_column()

    tasks: Mapped[List['Tasks']] = relationship(back_populates='link')

    __table_args__ = (
        UniqueConstraint('twitter_username', 'webhook_url'),
        Index('idx_links_username', 'twitter_username'),
    )


class Tweet(MyBase):
    __tablename__ = 'tweets'
    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column()
    snowflake: Mapped[int] = mapped_column(BigInteger)
    type: Mapped[TweetMode] = mapped_column(Enum(TweetMode))

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

    link: Mapped['Link'] = relationship(back_populates='tasks')
    tweet: Mapped['Tweet'] = relationship(back_populates='tasks')

    __table_args__ = (
        UniqueConstraint('link_id', 'tweet_id'),
        Index('idx_tasks_lookup', 'link_id', 'tweet_id'),
    )
