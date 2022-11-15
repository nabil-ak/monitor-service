import random
import traceback
import time

from monitors import aboutyou,shopify,cultura,micromania,popinabox,popito,wethenew,svd,prodirectsoccer,prodirectsoccer_release,eleventeamsports,magento,asos,kickz
from multiprocessing import Process
from threading import Thread
from random_user_agent.params import SoftwareName, HardwareType
from random_user_agent.user_agent import UserAgent
from user_agent import getcurrentChromeUseragent
from proxymanager import ProxyManager

import database

cookgroups = database.getGroups()
settings = database.getSettings()
ProxyManager.updateProxys()

monitorPool = []

def updateData():
    """
    Check settings, groups and proxys every 20 seconds for update
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

        if settings != newSettings or newCookgroups != cookgroups or ProxyManager.updateProxys():
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

    #Get newest Chrome Useragent
    chrome_user_agent = getcurrentChromeUseragent()

    #Create all Asos Monitors
    ASOSREGIONS = [["de","eur"], ["fr","eur"], ["es","eur"] , ["it","eur"], ["com","gbp"], ["roe","eur"], ["us","usd"]]
    for region in ASOSREGIONS:
        a = asos.asos(groups=cookgroups,skus=settings["asos"]["skus"],delay=settings["asos"]["delay"],region=region[0],currency=region[1],user_agents=user_agents,proxymanager=ProxyManager())
        monitorPool.append(Process(target=a.monitor))
    
    #Create all About You Monitors
    ABOUTYOUSTORES = [["DE",139],["CH",431],["FR",658],["ES",670],["IT",671],["PL",550],["CZ",554],["SK",586],["NL",545],["BE",558],["AT",200],["SE",655],["IE",657]]
    for store in ABOUTYOUSTORES:
        a = aboutyou.aboutyou(cookgroups,store[0],store[1],chrome_user_agent,ProxyManager(),settings["aboutyou"]["delay"],settings["aboutyou"]["keywords"],settings["aboutyou"]["blacksku"],settings["aboutyou"]["whitesku"])
        monitorPool.append(Process(target=a.monitor))
    
    #Create all Shopify Monitors
    shopifyGlobal = settings["shopify"]
    for s in shopifyGlobal["sites"]:
        """
        Check if keywords are set if so combine them with global keywords otherwise just use the global keywords if "local" keywords dosent exist.
        """
        if "keywords" in s:
            if not s["keywords"]:
                keywords = s["keywords"]
            else:
                keywords = s["keywords"]+shopifyGlobal["keywords"]
        else:
            keywords = shopifyGlobal["keywords"]
        
        """
        Check if tags are set if so combine them with global tags otherwise just use the global tags if "local" tags dosent exist.
        """
        if "tags" in s:
            if not s["tags"]:
                tags = s["tags"]
            else:
                tags = s["tags"]+shopifyGlobal["tags"]
        else:
            tags = shopifyGlobal["tags"]

        """
        Check if blackskus are set if so combine them with global blackskus otherwise just use the global blackskus if "local" blackskus dosent exist.
        """
        if "blacksku" in s:
            if not s["blacksku"]:
                blacksku = s["blacksku"]
            else:
                blacksku = s["blacksku"]+shopifyGlobal["blacksku"]
        else:
            blacksku = shopifyGlobal["blacksku"]

        """
        Check if negativkeywords are set if so combine them with global negativkeywords otherwise just use the global negativkeywords if "local" negativkeywords dosent exist.
        """
        if "negativkeywords" in s:
            if not s["negativkeywords"]:
                negativkeywords = s["negativkeywords"]
            else:
                negativkeywords = s["negativkeywords"]+shopifyGlobal["negativkeywords"]
        else:
            negativkeywords = shopifyGlobal["negativkeywords"]

        delay = shopifyGlobal["delay"] if "delay" not in s else s["delay"]
        shopifyProcess = shopify.shopify(groups=cookgroups,site=s["name"],url=s["url"],user_agents=user_agents,delay=delay,keywords=keywords,negativkeywords=negativkeywords,tags=tags,blacksku=blacksku,proxymanager=ProxyManager())
        monitorPool.append(Process(target=shopifyProcess.monitor))

    #Create all Magento Monitors
    '''
    magentoMonitores = ["topps"]

    for s in magentoMonitores:
        magentoProcess = magento.magento(groups=cookgroups,site=s,url=settings[s]["url"],store_id=settings[s]["store_id"],user_agent=chrome_user_agent,delay=settings[s]["delay"],keywords=settings[s]["keywords"],proxys=proxys,blacksku=settings[s]["blacksku"])
        monitorPool.append(Process(target=magentoProcess.monitor))'''
    
    #Create Cultura Monitor
    #culturaProcess = cultura.cultura(groups=cookgroups,user_agents=[{"user_agent":chrome_user_agent}],querys=settings["cultura"]["query"],delay=settings["cultura"]["delay"],blacksku=settings["cultura"]["blacksku"])
    #monitorPool.append(Process(target=culturaProcess.monitor))
    
    #Create Micromania Monitor
    micromaniaProcess = micromania.micromania(groups=cookgroups,user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}],querys=settings["micromania"]["query"],delay=settings["micromania"]["delay"],blacksku=settings["micromania"]["blacksku"])
    monitorPool.append(Process(target=micromaniaProcess.monitor))
    
    #Create Popinabox Monitor
    popinaboxProcess = popinabox.popinabox(groups=cookgroups,user_agents=user_agents,querys=settings["popinabox"]["query"],delay=settings["popinabox"]["delay"],blacksku=settings["popinabox"]["blacksku"],proxymanager=ProxyManager())
    monitorPool.append(Process(target=popinaboxProcess.monitor))
    
    #Create Popito Monitor
    #popitoProcess = popito.popito(groups=cookgroups,user_agents=user_agents,querys=settings["popito"]["query"],delay=settings["popito"]["delay"],blacksku=settings["popito"]["blacksku"])
    #monitorPool.append(Process(target=popitoProcess.monitor))
    
    #Create all Wethenew Monitor
    for endpoint in ["products", "sell-nows", "consignment-slots"]:
        wethenewProcess = wethenew.wethenew(groups=cookgroups,endpoint=endpoint,user_agent=chrome_user_agent,blacksku=settings["wethenew"]["blacksku"],delay=settings["wethenew"]["delay"],keywords=settings["wethenew"]["keywords"],proxymanager=ProxyManager(["theproxyclub"]))
        monitorPool.append(Process(target=wethenewProcess.monitor))

    #Create SVD Monitor
    svdProcess = svd.svd(groups=cookgroups,user_agents=user_agents,delay=settings["svd"]["delay"],keywords=settings["svd"]["keywords"],blacksku=settings["svd"]["blacksku"],proxymanager=ProxyManager(["round"]))
    monitorPool.append(Process(target=svdProcess.monitor))
    
    #Create kickz Monitor
    for region in settings["kickz"]["regions"]:
        kickzProcess = kickz.kickz(groups=cookgroups,region=region["region"],regionname=region["name"],user_agent=chrome_user_agent,delay=settings["kickz"]["delay"],keywords=settings["kickz"]["keywords"],blacksku=settings["kickz"]["blacksku"],proxymanager=ProxyManager(["round","theproxyclub"]))
        monitorPool.append(Process(target=kickzProcess.monitor))

    #Create prodirectsoccer Monitor
    prodirectsoccerProcess = prodirectsoccer.prodirectsoccer(groups=cookgroups,user_agent=chrome_user_agent,querys=settings["prodirectsoccer"]["query"],delay=settings["prodirectsoccer"]["delay"],blacksku=settings["prodirectsoccer"]["blacksku"],proxymanager=ProxyManager(["round"]))
    monitorPool.append(Process(target=prodirectsoccerProcess.monitor))
    
    prodirect = [["prodirectsoccer", "soccerengb"], ["prodirectsport","sportengb"], ["prodirectselect", "selectengb"], ["prodirectbasketball", "basketballengb"], ["prodirectfit", "fitengb"]]
    #Create prodirectsoccer_release Monitors
    for p in prodirect:
        prodirectsoccer_release_Process = prodirectsoccer_release.prodirectsoccer_release(site=p[0],releasecategory=p[1],groups=cookgroups,user_agents=user_agents,querys=settings["prodirectsoccer_release"]["query"],delay=settings["prodirectsoccer_release"]["delay"],blacksku=settings["prodirectsoccer_release"]["blacksku"],proxymanager=ProxyManager(["round","theproxyclub"]))
        monitorPool.append(Process(target=prodirectsoccer_release_Process.monitor))

    """
    #Create all other prodirect Monitor
    prodirect = [["prodirectselect", "selectengb"], ["prodirectbasketball", "basketballengb"], ["prodirectfit", "fitengb"]]
    for p in prodirect:
        prodirectProcess = prodirectsoccer_other.prodirectsoccer_other(name=p[0], releasecategory= p[1], groups=cookgroups,user_agents=user_agents,querys=settings["prodirectsoccer"]["query"],delay=settings["prodirectsoccer"]["delay"],blacksku=settings["prodirectsoccer"]["blacksku"],proxymanager=ProxyManager(["round"]))
        monitorPool.append(Process(target=prodirectProcess.monitor))"""

    #Create eleventeamsports Monitor
    eleventeamsportsProcess = eleventeamsports.eleventeamsports(groups=cookgroups,user_agent=chrome_user_agent,delay=settings["eleventeamsports"]["delay"],querys=settings["eleventeamsports"]["query"],blacksku=settings["eleventeamsports"]["blacksku"],proxymanager=ProxyManager())
    monitorPool.append(Process(target=eleventeamsportsProcess.monitor))
    
    #Start all Monitors
    for mon in monitorPool:
        mon.start()

if __name__ == "__main__":
    #Start Monitors
    startMonitors()

    #Check if new Group was added or updated and also check if settings was updated
    Thread(target=updateData).start()


