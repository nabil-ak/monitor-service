import time

TIMEOUT = 30
PINGDELAY = 10

class timeout:
    def __init__(self):
        self.pings = []
    
    def ping(self,product):
        """
        Check if same product with same sizes was already pinged in the last 10 seconds if so timeout product for 30 seconds.
        """
        for ping in self.pings:
            if ping["product"] == product:
                if ping["timeout"] >= time.time():
                    return False
                if ping["lastpingtimeout"] >= time.time():
                    ping["timeout"] = time.time()+TIMEOUT
                    return False
                ping["lastpingtimeout"] = time.time()+PINGDELAY
                return True

        self.pings.append({
            "product":product,
            "lastpingtimeout":time.time()+PINGDELAY,
            "timeout":-1
        })
        return True
                