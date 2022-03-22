from monitors import aboutyou,nbb,shopify
from threading import Thread
import json
import logging

logging.basicConfig(filename=f'monitor.log', filemode='a', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

cookgroups = json.load(open("groups.json"))
settings = json.load(open("settings.json"))
proxys = settings["proxys"]

if __name__ == "__main__":
    #Start About You Monitor
    Thread(target=aboutyou.monitor,args=(cookgroups,settings["aboutyou"]["delay"],settings["aboutyou"]["keywords"],proxys,settings["aboutyou"]["blacksku"],)).start()

    #Start NBB Monitor
    Thread(target=nbb.monitor,args=(cookgroups,settings["nbb"]["delay"],proxys,)).start()

    #Start KITH Monitor
    kith = shopify.shopify(groups=cookgroups,site="kith",url=settings["kith"]["url"],delay=settings["kith"]["delay"],keywords=settings["kith"]["keywords"],proxys=proxys)
    Thread(target=kith.monitor).start()


