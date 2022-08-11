from bs4 import BeautifulSoup
import requests
import random
import time
import traceback
import database

USERAGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"

def getcurrentChromeUseragent():
    """
    Get the latest Chrome User_Agent from whatismybrowser.com
    """
    try:
        proxys = database.getSettings()["ResiProxys"]
        proxy = random.choice(proxys)
        r = requests.get("https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome", proxies={"http": "http://"+proxy, "https": "http://"+proxy})
        output = BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
            print(f"[USERAGENT_Fetcher] Exception found: {traceback.format_exc()}")
            return USERAGENT
    return output.find('span', {'class': 'code'}).text