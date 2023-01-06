import requests as rq
import os

TLSCLIENT = f"http://{os.environ['GATEWAY']}:8082"


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

def get(url, headers={}, proxies={}, timeout=10, **kargs):
    """
    get request wrapper
    """
    headers = addParamsToHeader(url=url, headers=headers, proxies=proxies)
    
    res = rq.get(TLSCLIENT, headers=headers, timeout=timeout, **kargs)
    
    res = parseCookies(res, url)

    return res

def post(url, headers={}, proxies={}, timeout=10, **kargs):
    """
    post request wrapper
    """
    headers = addParamsToHeader(url=url, headers=headers, proxies=proxies)
    
    res = rq.post(TLSCLIENT, headers=headers, timeout=timeout, **kargs)
    
    res = parseCookies(res, url)

    return res

def head(url, headers={}, proxies={}, timeout=10, **kargs):
    """
    head request wrapper
    """
    headers = addParamsToHeader(url=url, headers=headers, proxies=proxies)
    
    res = rq.head(TLSCLIENT, headers=headers, timeout=timeout, **kargs)
    
    res = parseCookies(res, url)

    return res