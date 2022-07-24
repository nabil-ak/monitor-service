import random
import traceback
import time

from monitors import aboutyou,shopify,cultura,micromania,funkoeurope,popinabox,popito,wethenew,svd,prodirectsoccer,prodirectsoccer_other,eleventeamsports,wethenew_wtn
from multiprocessing import Process
from threading import Thread
from random_user_agent.params import SoftwareName, HardwareType
from random_user_agent.user_agent import UserAgent
from user_agent import getcurrentChromeUseragent

import database

cookgroups = database.getGroups()
settings = database.getSettings()
proxys = settings["ISPproxys"]
ISPproxys = settings["ISPproxys"]
monitorPool = []

def updateData():
    """
    Check settings and groups every 20 seconds for update
    """
    global settings,cookgroups,proxys
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
            proxys = settings["ISPproxys"]
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

    #Get newest Chrome Useragent
    chrome_user_agent = getcurrentChromeUseragent()

    
    #Create all About You Monitors
    ABOUTYOUSTORES = [["DE",139],["CH",431],["FR",658],["ES",670],["IT",671],["PL",550],["CZ",554],["SK",586],["NL",545],["BE",558],["AT",200],["SE",655],["IE",657]]
    for store in ABOUTYOUSTORES:
        a = aboutyou.aboutyou(cookgroups,store[0],store[1],user_agents,settings["aboutyou"]["delay"],settings["aboutyou"]["keywords"],proxys,settings["aboutyou"]["blacksku"],settings["aboutyou"]["whitesku"])
        monitorPool.append(Process(target=a.monitor))
    
    #Create all Shopify Monitors
    shopifyMonitores = ["kith", "slamjam", "asphaltgold", "esn", "packyard", "renouveau", "shoechapter", "stimm", "e5store", "beststreetclub", "sovtstudios", "sourcelugano", "canary---yellow", "sneakerbaas", "bouncewear", "thenextdoor"]

    for s in shopifyMonitores:
        blacksku = [] if "blacksku" not in settings[s] else settings[s]["blacksku"]
        shopifyProcess = shopify.shopify(groups=cookgroups,site=s,url=settings[s]["url"],user_agents=user_agents,delay=settings[s]["delay"],keywords=settings[s]["keywords"],proxys=proxys,blacksku=blacksku)
        monitorPool.append(Process(target=shopifyProcess.monitor))


    #Create NBB Monitor
    #nbbProcess = nbb.nbb(cookgroups,user_agents,settings["nbb"]["delay"],proxys)
    #monitorPool.append(Process(target=nbbProcess.monitor))
    
    #Create Zalando Monitor
    #zalandoProcess = zalando.zalando(groups=cookgroups,user_agents=user_agents,blacksku=settings["zalando"]["blacksku"],delay=settings["zalando"]["delay"],keywords=settings["zalando"]["keywords"],proxys=proxys)
    #monitorPool.append(Process(target=zalandoProcess.monitor))
    
    #Create Cultura Monitor
    culturaProcess = cultura.cultura(groups=cookgroups,user_agents=[{"user_agent":chrome_user_agent}],querys=settings["cultura"]["query"],delay=settings["cultura"]["delay"],blacksku=settings["cultura"]["blacksku"])
    monitorPool.append(Process(target=culturaProcess.monitor))
    
    #Create Micromania Monitor
    micromaniaProcess = micromania.micromania(groups=cookgroups,user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}],querys=settings["micromania"]["query"],delay=settings["micromania"]["delay"],blacksku=settings["micromania"]["blacksku"])
    monitorPool.append(Process(target=micromaniaProcess.monitor))
    
    #Create Funkoeurope Monitor
    funkoeuropeProcess = funkoeurope.funkoeurope(groups=cookgroups,site="funkoeurope",url=settings["funkoeurope"]["url"],user_agents=user_agents,delay=settings["funkoeurope"]["delay"],tags=settings["funkoeurope"]["tags"],proxys=proxys)
    monitorPool.append(Process(target=funkoeuropeProcess.monitor))
    
    #Create Popinabox Monitor
    popinaboxProcess = popinabox.popinabox(groups=cookgroups,user_agents=user_agents,querys=settings["popinabox"]["query"],delay=settings["popinabox"]["delay"],blacksku=settings["popinabox"]["blacksku"],proxys=proxys)
    monitorPool.append(Process(target=popinaboxProcess.monitor))
    
    #Create Popito Monitor
    popitoProcess = popito.popito(groups=cookgroups,user_agents=user_agents,querys=settings["popito"]["query"],delay=settings["popito"]["delay"],blacksku=settings["popito"]["blacksku"])
    monitorPool.append(Process(target=popitoProcess.monitor))
    
    #Create Wethenew Monitor
    wethenewProcess = wethenew.wethenew(groups=cookgroups,user_agent=chrome_user_agent,blacksku=settings["wethenew"]["blacksku"],delay=settings["wethenew"]["delay"],keywords=settings["wethenew"]["keywords"],proxys=proxys)
    monitorPool.append(Process(target=wethenewProcess.monitor))

    #Create Wethenew-WTN Monitor
    wethenew_wtnProcess = wethenew_wtn.wethenew_wtn(groups=cookgroups,user_agent=chrome_user_agent,blacksku=settings["wethenew_wtn"]["blacksku"],delay=settings["wethenew_wtn"]["delay"],keywords=settings["wethenew_wtn"]["keywords"],proxys=proxys)
    monitorPool.append(Process(target=wethenew_wtnProcess.monitor))

    #Create SVD Monitor
    svdProcess = svd.svd(groups=cookgroups,user_agents=user_agents,delay=settings["svd"]["delay"],keywords=settings["svd"]["keywords"],blacksku=settings["svd"]["blacksku"],proxys=proxys)
    monitorPool.append(Process(target=svdProcess.monitor))

    #Create prodirectsoccer Monitor
    prodirectsoccerProcess = prodirectsoccer.prodirectsoccer(groups=cookgroups,user_agents=user_agents,querys=settings["prodirectsoccer"]["query"],delay=settings["prodirectsoccer"]["delay"],blacksku=settings["prodirectsoccer"]["blacksku"],proxys=ISPproxys)
    monitorPool.append(Process(target=prodirectsoccerProcess.monitor))

    #Create all other prodirect Monitor
    prodirect = [["prodirectselect", "selectengb"], ["prodirectbasketball", "basketballengb"], ["prodirectfit", "fitengb"]]
    for p in prodirect:
        prodirectProcess = prodirectsoccer_other.prodirectsoccer_other(name=p[0], releasecategory= p[1], groups=cookgroups,user_agents=user_agents,querys=settings["prodirectsoccer"]["query"],delay=settings["prodirectsoccer"]["delay"],blacksku=settings["prodirectsoccer"]["blacksku"],proxys=ISPproxys)
        monitorPool.append(Process(target=prodirectProcess.monitor))

    #Create eleventeamsports Monitor
    eleventeamsportsProcess = eleventeamsports.eleventeamsports(groups=cookgroups,user_agents=user_agents,delay=settings["eleventeamsports"]["delay"],querys=settings["eleventeamsports"]["query"],blacksku=settings["eleventeamsports"]["blacksku"],proxys=proxys)
    monitorPool.append(Process(target=eleventeamsportsProcess.monitor))
    
    #Start all Monitors
    for mon in monitorPool:
        mon.start()

if __name__ == "__main__":
    #Start Monitors
    startMonitors()

    #Check if new Group was added or updated and also check if settings was updated
    Thread(target=updateData).start()


