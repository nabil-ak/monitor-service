import time
from copy import deepcopy

TIMEOUT = 30
PINGDELAY = 10

class timeout:
    def __init__(self,timeout=TIMEOUT,pingdelay=PINGDELAY):
        self.pings = []
        self.timeout = timeout
        self.pingdelay = pingdelay
    
    def ping(self,product):
        """
        Check if same product with same sizes was already pinged in the last 10 seconds if so timeout product for 30 seconds.
        """
        for ping in self.pings:
            if ping["product"] == product:
                if ping["timeout"] >= time.time():
                    return False
                if ping["lastpingtimeout"] >= time.time():
                    ping["timeout"] = time.time()+self.timeout
                    return False
                ping["lastpingtimeout"] = time.time()+self.pingdelay
                return True

        self.pings.append({
            "product":deepcopy(product),
            "lastpingtimeout":time.time()+self.pingdelay,
            "timeout":-1
        })
        return True
                