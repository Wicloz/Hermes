from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from time import sleep
from sqlalchemy.orm import Session
from settings import ENGINE, TWITTER_TOKEN
from database import Link, Tweet, Tasks, TweetMode, WebhookMode
from datetime import datetime
from selenium.webdriver.common.keys import Keys
import requests


def get_first_new_window(browser, exclude):
    for window in browser.window_handles:
        if window not in exclude:
            return window
    return None


def run_after_browser_open(browser):
    browser.get('https://twitter.com/')
    browser.add_cookie({
        'name': 'auth_token',
        'value': TWITTER_TOKEN,
        'domain': '.twitter.com',
    })

    registered_windows = set(browser.window_handles)
    twitter_user_windows = {}
    browser.get('about:blank')

    while True:
        with Session(ENGINE) as session:
            for username, window in twitter_user_windows.items():
                browser.switch_to.window(window)

                links = session.query(Link).filter(Link.twitter_username == username).all()

                if not links:
                    browser.close()
                    registered_windows.remove(window)
                    twitter_user_windows.pop(username)
                    continue

                for tweet in reversed(browser.find_elements(By.TAG_NAME, 'article')[:10]):
                    time = tweet.find_element(By.TAG_NAME, 'time').get_attribute('datetime')
                    time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.000Z')

                    type = TweetMode.TWEET
                    if 'reposted' in tweet.text:
                        type = TweetMode.RETWEET

                    print(f'Found {type.name} from {username} at {time}')

                    result = session.query(Tweet).filter(
                        (Tweet.timestamp == time) & (Tweet.username == username)
                    ).first()

                    if result is None:
                        tweet.send_keys(Keys.CONTROL + Keys.RETURN)
                        sleep(1)

                        browser.switch_to.window(get_first_new_window(browser, registered_windows))
                        snowflake = int(browser.current_url.split('/')[-1])
                        browser.close()
                        browser.switch_to.window(window)

                        result = Tweet(username=username, timestamp=time,
                                       snowflake=snowflake, type=type)
                        session.add(result)
                        session.commit()

                        print(f'> New snowflake "{snowflake}" registered')

                    embed_url = f'https://fxtwitter.com/{result.username}/status/{result.snowflake}'
                    verb = 'Tweeted'
                    if result.type == TweetMode.RETWEET:
                        verb = 'Retweeted'

                    for link in links:
                        if session.query(Tasks).filter(
                            (Tasks.link_id == link.id) & (Tasks.tweet_id == result.id)
                        ).exists():
                            continue

                        ping_prefix = ''
                        if link.webhook_pings:
                            ping_prefix = f'{link.webhook_pings}: '

                        if link.webhook_type == WebhookMode.DISCORD:
                            response = requests.post(link.webhook_url, json={
                                'content': f'{ping_prefix}{result.username} [{verb}]({embed_url})',
                            })

                        if link.webhook_type == WebhookMode.ROCKETCHAT:
                            response = requests.post(link.webhook_url, json={
                                'text': f'{ping_prefix}{result.username} [{verb}]({embed_url})',
                            })

                        if response.ok:
                            session.add(Tasks(link_id=link.id, tweet_id=result.id))
                            session.commit()

                browser.refresh()

        with Session(ENGINE) as session:
            for username in session.query(Link.twitter_username).distinct():
                username, = username

                if username in twitter_user_windows:
                    continue

                browser.execute_script(f'window.open("https://twitter.com/{username}");')
                twitter_user_windows[username] = get_first_new_window(browser, registered_windows)
                registered_windows.add(twitter_user_windows[username])

        sleep(60)


if __name__ == '__main__':
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    with webdriver.Firefox(options=options) as driver:
        run_after_browser_open(driver)
