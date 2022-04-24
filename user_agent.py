from bs4 import BeautifulSoup
import requests
import random
from database import getSettings

def getcurrentChromeUseragent():
    """
    Get the latest Chrome User_Agent from whatismybrowser.com
    """
    proxy = random.choice(getSettings()["ResiProxys"])
    r = requests.get("https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome", proxies={"http": proxy, "https": proxy})
    output = BeautifulSoup(r.text, 'html.parser')
    return output.find('span', {'class': 'code'}).text