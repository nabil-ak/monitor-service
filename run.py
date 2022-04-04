import random
import traceback
import time
from monitors import aboutyou,nbb,shopify,zalando,swatch,cultura
from multiprocessing import Process
from threading import Thread
from random_user_agent.params import SoftwareName, HardwareType
from random_user_agent.user_agent import UserAgent

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
            time.sleep(10)
            database.Connect()

        if settings != newSettings or newCookgroups != cookgroups:
            cookgroups = newCookgroups
            settings = newSettings
            print("[UPDATER] Restart Monitors")

            #Restart every Monitor
            for mon in monitorPool:
                #Stop them
                mon.terminate()
            monitorPool.clear()

            #Start them with new Settings
            startMonitors()
            
        time.sleep(20)

def startMonitors():
    """
    Start every Monitor in a Process
    """
    #Get 200 random User Agents
    software_names = [SoftwareName.CHROME.value]
    hardware_type = [HardwareType.MOBILE__PHONE]
    user_agents = random.choices(UserAgent(software_names=software_names, hardware_type=hardware_type).get_user_agents(), k=200)

    
    #Create all About You Monitors
    ABOUTYOUSTORES = [["DE",139],["CH",431],["FR",658],["ES",670],["IT",671],["PL",550],["CZ",554],["SK",586],["NL",545],["BE",558]]
    for store in ABOUTYOUSTORES:
        a = aboutyou.aboutyou(cookgroups,store[0],store[1],user_agents,settings["aboutyou"]["delay"],settings["aboutyou"]["keywords"],proxys,settings["aboutyou"]["blacksku"])
        monitorPool.append(Process(target=a.monitor))

    #Create NBB Monitor
    nbbProcess = nbb.nbb(cookgroups,user_agents,settings["nbb"]["delay"],proxys)
    monitorPool.append(Process(target=nbbProcess.monitor))

    #Create KITH Monitor
    kithProcess = shopify.shopify(groups=cookgroups,site="kith",url=settings["kith"]["url"],user_agents=user_agents,delay=settings["kith"]["delay"],keywords=settings["kith"]["keywords"],proxys=proxys)
    monitorPool.append(Process(target=kithProcess.monitor))

    #Create Zalando Monitor
    zalandoProcess = zalando.zalando(groups=cookgroups,user_agents=user_agents,blacksku=settings["zalando"]["blacksku"],delay=settings["zalando"]["delay"],keywords=settings["zalando"]["keywords"],proxys=proxys)
    monitorPool.append(Process(target=zalandoProcess.monitor))

    #Create Swatch Monitor
    swatchProcess = swatch.swatch(groups=cookgroups,user_agents=user_agents,proxys=proxys,delay=2)
    monitorPool.append(Process(target=swatchProcess.monitor))
    
    #Create Cultura Monitor
    culturaProcess = cultura.cultura(groups=cookgroups,user_agents=[{"user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36"}],querys=settings["cultura"]["query"],delay=settings["cultura"]["delay"])
    monitorPool.append(Process(target=culturaProcess.monitor))

    #Start all Monitors
    for mon in monitorPool:
        mon.start()

if __name__ == "__main__":
    #Start Monitors
    startMonitors()

    #Check if new Group was added or updated and also check if settings was updated
    Thread(target=updateData).start()


