import requests
import json
import cloudscraper

s = requests.Session()

def makeReq(url, headers={}, payload={}):
    if(payload != {}):  #if payload setted do post, if not do get
        res = s.post(url, headers=headers, data=payload)
        
        #append session cookies to session:
        sescookies = res.headers["session-cookies"].split('; ')
        for x in range(len(sescookies)):
            if sescookies[x] == "":
                continue
            domain = url.split('://')[1]
            if '/' in domain:
                domain = domain.split('/')[0]
            s.cookies.set(sescookies[x].split('=')[0], sescookies[x].split('=')[1], domain=domain)
    else:
        res = s.get(url, headers=headers)
        
        #append session cookies to session:
        sescookies = res.headers["session-cookies"].split('; ')
        for x in range(len(sescookies)):
            if sescookies[x] == "":
                continue
            domain = url.split('://')[1]
            if '/' in domain:
                domain = domain.split('/')[0]
            s.cookies.set(sescookies[x].split('=')[0], sescookies[x].split('=')[1], domain=domain)
    return res

headersGet = {
    'Poptls-Proxy':'http://porter683:131RNU@109.160.39.171:61234/',
    'Poptls-Url': 'https://tls.peet.ws/api/all',
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'if-modified-since': 'Mon, 29 Aug 2022 14:39:20 GMT',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="104"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36',
}

scraper = cloudscraper.create_scraper(browser={"custom": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36"}, debug=True)
#getReq = makeReq('http://202.61.192.38:8082', headers=headersGet)
getReq = scraper.get("https://tls.peet.ws/api/all"
)
print(getReq.text)
print(getReq.status_code)