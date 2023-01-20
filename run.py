import traceback
import time
import database
import copy

from monitors import aboutyou,shopify,wethenew,svd,prodirectsoccer,prodirectsoccer_release,eleventeamsports,asos,kickz,shopify_priceerror
from threading import Thread
from proxymanager import ProxyManager


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


def filterGroups(sites):
    """
    Return groups that have a webhook of a specific site
    """
    filteredGroups = []
    for group in cookgroups:
        if any(site in group for site in sites):
            filteredGroups.append(group)
    
    return filteredGroups

def startMonitors():
    """
    Start every Monitor in a Process
    """

    #Create all Asos Monitors
    for region in settings["asos"]["regions"]:
        monitorPool.append(asos.asos(groups=filterGroups(["asos"]),settings=settings["asos"],region=region[0],currency=region[1]))
    
    #Create all About You Monitors
    for store in settings["aboutyou"]["stores"]:
        monitorPool.append(aboutyou.aboutyou(groups=filterGroups(["aboutyou"]), settings=settings["aboutyou"], store=store[0], storeid=store[1]))
    
    #Create all Shopify Monitors
    shopifyGlobal = copy.deepcopy(settings["shopify"])
    for s in shopifyGlobal["sites"]:
        if "keywords" in s and s["keywords"]:
            s["keywords"] = s["keywords"]+shopifyGlobal["keywords"]
        else:
            s["keywords"] = shopifyGlobal["keywords"]
        
        if "tags" in s and s["tags"]:
            s["tags"] = s["tags"]+shopifyGlobal["tags"]
        else:
            s["tags"] = shopifyGlobal["tags"]

       
        if "blacksku" in s and s["blacksku"]:
            s["blacksku"] = s["blacksku"]+shopifyGlobal["blacksku"]
        else:
            s["blacksku"] = shopifyGlobal["blacksku"]

        if "negativkeywords" in s and s["negativkeywords"]:
            s["negativkeywords"] = s["negativkeywords"]+shopifyGlobal["negativkeywords"]
        else:
            s["negativkeywords"] = shopifyGlobal["negativkeywords"]

        if "delay" not in s: 
            s["delay"] = shopifyGlobal["delay"]

        s["proxys"] = shopifyGlobal["proxys"]
        monitorPool.append(shopify.shopify(groups=filterGroups([s["name"], "shopify"]),settings=s))

    #Create all Wethenew Monitor
    endpoints = ["products", "sell-nows", "consignment-slots"]
    for ep in endpoints:
        monitorPool.append(wethenew.wethenew(groups=filterGroups(["wethenew-"+ep]),endpoint=ep,settings=settings["wethenew"]))

    #Wethenew Price Error
    monitorPool.append(shopify_priceerror.shopify_priceerror(groups=filterGroups(["wethenew_priceerror"]),settings=settings["wethenew_priceerror"]))

    #Create SVD Monitor
    monitorPool.append(svd.svd(groups=filterGroups(["svd"]),settings=settings["svd"]))
    
    #Create kickz Monitor
    for region in settings["kickz"]["regions"]:
        monitorPool.append(kickz.kickz(groups=filterGroups(["kickz"]),region=region["region"],regionname=region["name"],settings=settings["kickz"]))

    #Create prodirectsoccer Monitor
    monitorPool.append(prodirectsoccer.prodirectsoccer(groups=filterGroups(["prodirectsoccer"]),settings=settings["prodirectsoccer"]))
    
    #Create prodirectsoccer_release Monitors
    for p in settings["prodirectsoccer_release"]["sites"]:
        monitorPool.append(prodirectsoccer_release.prodirectsoccer_release(groups=filterGroups(["prodirectsoccer_release"]),site=p[0],releasecategory=p[1],settings=settings["prodirectsoccer_release"]))

    #Create eleventeamsports Monitor
    monitorPool.append(eleventeamsports.eleventeamsports(groups=filterGroups(["eleventeamsports"]),settings=settings["eleventeamsports"]))
    
    #Start all Monitors
    for mon in monitorPool:
        mon.start()

if __name__ == "__main__":
    #Start Monitors
    startMonitors()

    #Check if new Group was added or updated and also check if settings was updated
    Thread(target=updateData).start()

