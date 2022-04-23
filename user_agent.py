from bs4 import BeautifulSoup
import requests

def getcurrentChromeUseragent():
    r = requests.get("https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome")
    output = BeautifulSoup(r.text, 'html.parser')
    return output.find('span', {'class': 'code'}).text
