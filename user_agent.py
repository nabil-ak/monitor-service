from bs4 import BeautifulSoup
import requests
import random
import time
import traceback
import database

def getcurrentChromeUseragent():
    """
    Get the latest Chrome User_Agent from whatismybrowser.com
    """
    try:
        proxys = database.getSettings()["ResiProxys"]
    except Exception as e:
            print(f"[DATABASE] Exception found: {traceback.format_exc()}")
            time.sleep(10)
            database.Connect()
    proxy = random.choice(proxys)
    r = requests.get("https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome", proxies={"http": "http://"+proxy, "https": "http://"+proxy})
    output = BeautifulSoup(r.text, 'html.parser')
    return output.find('span', {'class': 'code'}).text