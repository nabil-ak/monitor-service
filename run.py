import traceback
import time
from monitors import aboutyou,nbb,shopify
from threading import Thread
import logging

logging.basicConfig(filename=f'monitor.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

import database

cookgroups = database.getGroups()
settings = database.getSettings()
proxys = settings["proxys"]
monitorPool = []

def updateData():
    """
    Check settings and groups every 20 seconds for update
    """
    global settings,cookgroups
    while True:
        try:
            newCookgroups = database.getGroups()
            newSettings = database.getSettings()
        except Exception as e:
            print(f"[DATABASE] Exception found: {traceback.format_exc()}")
            logging.error(e)
            time.sleep(10)
            database.Connect()

        if settings != newSettings or newCookgroups != cookgroups:
            cookgroups = newCookgroups
            settings = newSettings
            #Update every Monitor
            for mon in monitorPool:
                mon.update(cookgroups,settings)
        time.sleep(20)

if __name__ == "__main__":
    #Create About You Monitor
    aboutyou = aboutyou.aboutyou(cookgroups,settings["aboutyou"]["delay"],settings["aboutyou"]["keywords"],proxys,settings["aboutyou"]["blacksku"])
    monitorPool.append(aboutyou)

    #Create NBB Monitor
    nbb = nbb.nbb(cookgroups,settings["nbb"]["delay"],proxys)
    monitorPool.append(nbb)

    #Create KITH Monitor
    kith = shopify.shopify(groups=cookgroups,site="kith",url=settings["kith"]["url"],delay=settings["kith"]["delay"],keywords=settings["kith"]["keywords"],proxys=proxys)
    monitorPool.append(kith)

    #Start all Monitors
    for mon in monitorPool:
        Thread(target=mon.monitor).start()

    #Check if new Group was added or updated and also check if settings was updated
    Thread(target=updateData).start()


