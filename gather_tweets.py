from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from time import sleep
from sqlalchemy.orm import Session
from settings import ENGINE, TWITTER_TOKEN
from database import Link, Tweet, Tasks, TweetMode
from datetime import datetime
from selenium.webdriver.common.keys import Keys


def get_first_window_not_in_list(exclude):
    for window in browser.window_handles:
        if window not in exclude:
            return window
    return None


if __name__ == '__main__':
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    browser = webdriver.Firefox(options=options)

    browser.get('https://twitter.com/')
    browser.add_cookie({
        'name': 'auth_token',
        'value': TWITTER_TOKEN,
        'domain': '.twitter.com',
    })

    initial_windows = set(browser.window_handles)
    windows = {}

    with Session(ENGINE) as session:
        for username in session.query(Link.twitter_username).distinct():
            username, = username
            browser.execute_script(f'window.open("https://twitter.com/{username}");')
            windows[username] = get_first_window_not_in_list(initial_windows)
            initial_windows.add(windows[username])

    browser.close()
    sleep(10)

    while True:
        with Session(ENGINE) as session:
            for username, window in windows.items():
                browser.switch_to.window(window)

                links = session.query(Link).filter(Link.twitter_username == username).all()
                tweets = browser.find_elements(By.TAG_NAME, 'article')[:10]

                for tweet in tweets:
                    time = tweet.find_element(By.TAG_NAME, 'time').get_attribute('datetime')
                    time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.000Z')

                    type = TweetMode.TWEET
                    if 'reposted' in tweet.text:
                        type = TweetMode.RETWEET

                    result = session.query(Tweet).filter(
                        (Tweet.timestamp == time) & (Tweet.username == username)
                    ).first()

                    if result is None:
                        tweet.send_keys(Keys.CONTROL + Keys.RETURN)
                        sleep(1)

                        browser.switch_to.window(get_first_window_not_in_list(initial_windows))
                        snowflake = int(browser.current_url.split('/')[-1])
                        browser.close()
                        browser.switch_to.window(window)

                        result = Tweet(username=username, timestamp=time,
                                       snowflake=snowflake, type=type)
                        session.add(result)
                        session.commit()

                    for link in links:
                        if session.query(Tasks).filter(
                            (Tasks.link_id == link.id) & (Tasks.tweet_id == result.id)
                        ).first() is None:
                            session.add(Tasks(link_id=link.id, tweet_id=result.id))
                    session.commit()

        browser.refresh()
        sleep(60)
