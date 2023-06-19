import requests as rq
import os

DOCSCLIENT = f"http://{os.environ['GATEWAY']}:4501/api/v2/safeFetch"


def get(url, timeout=10, **kargs):
    """
    get request wrapper
    """
    
    res = rq.post(DOCSCLIENT, json={
        "url":url
    }, timeout=timeout, **kargs)
    res.raise_for_status()
    res = res.json()

    if res["Success"]:
        return res["Content"]
    
    return None