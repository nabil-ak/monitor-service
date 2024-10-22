import traceback
import time
import database
import copy

from monitors import aboutyou,shopify,wethenew,svd,prodirectsoccer,prodirectsoccer_release,eleventeamsports,asos,newbalance,shopify_priceerror,demandware_wishlist_morelist,bstn,courir,salomen
from threading import Thread
from proxymanager import ProxyManager

cookgroups = database.getGroups()
originalSettings = database.getSettings()
ProxyManager.updateProxys()

monitorPool = []

def updateData():
    """
    Check settings, groups and proxys every 20 seconds for update
    """
    global originalSettings,cookgroups,proxys
    while True:
        try:
            newCookgroups = database.getGroups()
            newSettings = database.getSettings()
        except Exception as e:
            print(f"[DATABASE] Exception found: {traceback.format_exc()}")
            time.sleep(10)
            database.Connect()

        if originalSettings != newSettings or newCookgroups != cookgroups or ProxyManager.updateProxys():
            cookgroups = newCookgroups
            originalSettings = newSettings
            print("[UPDATER] Restart Monitors")

            #Restart every Monitor
            for mon in monitorPool:
                if isinstance(mon, Thread):
                    mon.stop.set()
                else:
                    mon.terminate()

            #Wait for each Monitor to stop
            for mon in monitorPool:
                if isinstance(mon, Thread) and mon.is_alive():
                    mon.join()
            
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

    settings = copy.deepcopy(originalSettings)

    """
    #Create all Asos Monitors
    for region in settings["asos"]["regions"]:
        monitorPool.append(asos.asos(groups=filterGroups(["asos","asos_"+region[0]]),settings=settings["asos"],region=region[0],currency=region[1]))
    
    #Create all About You Monitors
    for store in settings["aboutyou"]["stores"]:
        monitorPool.append(aboutyou.aboutyou(groups=filterGroups(["aboutyou"]), settings=settings["aboutyou"], store=store[0], storeid=store[1]))
    
    #Create all Shopify Monitors
    shopifyGlobal = settings["shopify"]
    for s in shopifyGlobal["sites"]:
        if "keywords" in s:
            if s["keywords"]:
                s["keywords"] = s["keywords"]+shopifyGlobal["keywords"]
        else:
            s["keywords"] = shopifyGlobal["keywords"]
        
        if "tags" in s:
            if s["tags"]:
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

    #Create bstn Monitor
    monitorPool.append(bstn.bstn(groups=filterGroups(["bstn"]),settings=settings["bstn"]))

    #Start all Demandware Wishlist MoreList Monitors
    for site in settings["demandware_wishlist_morelist"]:
        monitorPool.append(demandware_wishlist_morelist.demandware_wishlist_morelist(groups=filterGroups([site["name"]]), settings=site))

    #Create newbalance Monitor
    monitorPool.append(newbalance.newbalance(groups=filterGroups(["newbalance"]), settings=settings["newbalance"]))

    #Create prodirectsoccer Monitor
    monitorPool.append(prodirectsoccer.prodirectsoccer(groups=filterGroups(["prodirectsoccer"]),settings=settings["prodirectsoccer"]))
    
    #Create prodirectsoccer_release Monitors
    for p in settings["prodirectsoccer_release"]["sites"]:
        monitorPool.append(prodirectsoccer_release.prodirectsoccer_release(groups=filterGroups(["prodirectsoccer_release"]),site=p[0],releasecategory=p[1],settings=settings["prodirectsoccer_release"]))

    #Create eleventeamsports Monitor
    monitorPool.append(eleventeamsports.eleventeamsports(groups=filterGroups(["eleventeamsports"]),settings=settings["eleventeamsports"]))

    #Create courir Monitor
    monitorPool.append(courir.courir(groups=filterGroups(["courir"]), settings=settings["courir"]))

    #Create prodirectsoccer Monitor
    monitorPool.append(salomen.salomen(groups=filterGroups(["salomen"]),settings=settings["salomen"]))

    """

    endpoints = ["products", "sell-nows", "consignment-slots"]
    for ep in endpoints:
        monitorPool.append(wethenew.wethenew(groups=filterGroups(["wethenew-"+ep]),endpoint=ep,settings=settings["wethenew"]))

    #Start all Monitors
    for mon in monitorPool:
        mon.start()

if __name__ == "__main__":
    #Start Monitors
    startMonitors()

    #Check if new Group was added or updated and also check if settings was updated
    updateData()