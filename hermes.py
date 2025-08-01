from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from time import sleep
from sqlalchemy.orm import Session
from settings import ENGINE, TWITTER_TOKEN
from database import Link, Tweet, Tasks, WebhookMode
from datetime import datetime
from selenium.webdriver.common.keys import Keys
import requests
from jinja2 import Template
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException


def get_first_new_window(browser, exclude):
    for window in browser.window_handles:
        if window not in exclude:
            return window
    return None


def run_after_browser_open(browser, session):
    browser.get('https://x.com/')
    browser.add_cookie({
        'name': 'auth_token',
        'value': TWITTER_TOKEN,
        'domain': '.x.com',
    })

    registered_windows = set(browser.window_handles)
    twitter_user_windows = {}
    browser.get('about:blank')

    while True:
        for username, window in twitter_user_windows.items():
            browser.switch_to.window(window)

            links = session.query(Link).filter(Link.twitter_username == username).all()

            if not links:
                browser.close()
                registered_windows.remove(window)
                twitter_user_windows.pop(username)
                continue

            browser.execute_script('window.scrollTo(0, 1000);')
            sleep(2)
            browser.execute_script('window.scrollTo(0, 0000);')
            sleep(8)

            for tweet in reversed(browser.find_elements(By.TAG_NAME, 'article')[:10]):
                try:
                    time = tweet.find_element(By.TAG_NAME, 'time').get_attribute('datetime')
                except (NoSuchElementException, StaleElementReferenceException):
                    continue

                time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.000Z')
                print(f'Found timeline item from {username} at {time}')

                result = session.query(Tweet).filter(
                    (Tweet.timeline_when == time) & (Tweet.timeline_user == username)
                ).first()

                if result is None:
                    tweet.send_keys(Keys.CONTROL + Keys.RETURN)
                    browser.switch_to.window(get_first_new_window(browser, registered_windows))

                    while browser.current_url == 'about:blank':
                        sleep(1)

                    _, _, _, tweet_user, _, tweet_id = browser.current_url.split('/')
                    browser.close()
                    browser.switch_to.window(window)

                    result = Tweet(timeline_user=username, timeline_when=time,
                                   tweet_user=tweet_user, tweet_id=tweet_id)
                    session.add(result)
                    session.commit()

                    print(f'> New tweet "{tweet_id}" by "{tweet_user}" registered')

                for link in links:
                    if session.query(Tasks).filter(
                        (Tasks.link_id == link.id) & (Tasks.tweet_id == result.id)
                    ).count():
                        continue

                    message = Template(link.template).render(tweet=result)

                    if link.webhook_type == WebhookMode.DISCORD:
                        response = requests.post(link.webhook_url, json={'content': message})

                    if link.webhook_type == WebhookMode.ROCKETCHAT:
                        response = requests.post(link.webhook_url, json={'text': message})

                    if response.ok:
                        session.add(Tasks(link_id=link.id, tweet_id=result.id))
                        session.commit()

        for username in session.query(Link.twitter_username).distinct():
            username, = username

            if username in twitter_user_windows:
                continue

            browser.execute_script(f'window.open("https://x.com/{username}");')
            twitter_user_windows[username] = get_first_new_window(browser, registered_windows)
            registered_windows.add(twitter_user_windows[username])


if __name__ == '__main__':
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    with webdriver.Firefox(options=options) as driver:
        with Session(ENGINE) as session:
            run_after_browser_open(driver, session)
