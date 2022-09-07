import requests as rq

if __name__ == "__main__":
    TLSCLIENT = "http://202.61.192.38:8082"
else:
    TLSCLIENT = "http://127.0.0.1:8082"


def addParamsToHeader(url, headers, proxies):
    """
    Add the url and the proxy to the headers to let the tlsclient use them
    """
    if proxies != {}:
        headers["Poptls-Proxy"] = proxies["http"]
    headers["Poptls-Url"] = url
    return headers

def parseCookies(res, url):
    """
    Parse the cookies from the headers into the cookiejar of the response
    """
    res.cookies.clear()
    sescookies = res.headers["session-cookies"].split('; ')
    for x in range(len(sescookies)):
        if sescookies[x] == "":
            continue
        domain = url.split('://')[1]
        if '/' in domain:
            domain = domain.split('/')[0]
        res.cookies.set(sescookies[x].split('=')[0], sescookies[x].split('=')[1], domain=domain)
    del res.headers["session-cookies"]
    return res

def get(url, headers={}, proxies={}, timeout=10):
    """
    get request wrapper
    """
    headers = addParamsToHeader(url=url, headers=headers, proxies=proxies)
    
    res = rq.get(TLSCLIENT, headers=headers, timeout=timeout)
    
    res = parseCookies(res, url)

    return res

def post(url, headers={}, data={}, proxies={}, timeout=10):
    """
    post request wrapper
    """
    headers = addParamsToHeader(url=url, headers=headers, proxies=proxies)
    
    res = rq.post(TLSCLIENT, headers=headers, data=data, timeout=timeout)
    
    res = parseCookies(res, url)

    return res

if __name__ == "__main__":
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
    }
    getReq = get('https://api-sell.wethenew.com/products?skip=100&take=100&onlyWanted=true', headers=headers
    )
    print(getReq.text)
    print(getReq.status_code)
    print(getReq.cookies)
    print(getReq.headers)