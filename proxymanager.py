import database
import traceback
import time
import random
from multiprocessing import Lock

PROXYS = {}

class ProxyManager():
    @staticmethod
    def updateProxys():
        """
        Fetch newest proxys from the database
        """
        global PROXYS
        try:
            newProxys = database.getProxys()
        except Exception as e:
            print(f"[DATABASE] Exception found: {traceback.format_exc()}")
            time.sleep(10)
            database.Connect()
            return ProxyManager.updateProxys()
            

        if newProxys != PROXYS:
            PROXYS = newProxys
            return True
        else:
            return False


    def __init__(self, proxygroups=[]):
        self.proxygroups = proxygroups
        self.proxys = []
        self.lock = Lock()
        if self.proxygroups:
            for group in PROXYS:
                if group in self.proxygroups:
                    self.proxys.append(PROXYS[group])
        else:
            self.proxys = PROXYS.values()
        self.proxys = sum(self.proxys, [])
        self.currentProxy = random.randint(0, len(self.proxys)-1)


    def next(self):
        """
        Get the next Proxy
        """
        with self.lock:
            self.currentProxy = 0 if self.currentProxy >= (len(self.proxys) - 1) or not self.proxys else self.currentProxy + 1

        return {
        "http":f"http://{self.proxys[self.currentProxy]}",
        "https":f"http://{self.proxys[self.currentProxy]}"
        } if self.proxys else {}