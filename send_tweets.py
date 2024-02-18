import discord
from discord.ext import tasks
from sqlalchemy.orm import Session
from database import Tasks, TweetMode
from settings import ENGINE, DISCORD_TOKEN


class MyClient(discord.Client):
    async def setup_hook(self):
        self.handle_all_db_tasks.start()

    @tasks.loop(seconds=10)
    async def handle_all_db_tasks(self):
        await self.wait_until_ready()

        with Session(ENGINE) as session:
            tasks = sorted(session.query(Tasks).filter(Tasks.sent == False),
                           key=lambda x: x.tweet.timestamp)

            for task in tasks:
                embed_url = f'https://fxtwitter.com/{task.link.twitter_username}/status/{task.tweet.snowflake}'

                verb = 'Tweeted'
                if task.tweet.type == TweetMode.RETWEET:
                    verb = 'Retweeted'

                await self.get_channel(task.link.discord_channel).send(
                    f'{task.link.twitter_username} [{verb}]({embed_url})'
                )

                task.sent = True
                session.commit()


if __name__ == '__main__':
    client = MyClient(intents=None)
    client.run(DISCORD_TOKEN)
