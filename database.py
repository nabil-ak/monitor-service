from pymongo import MongoClient
import traceback
import time
import os

def getGroups():
    """
    Get all Cooking Groups from the Database
    """
    groups = []
    for group in client["groups"].find({},{'_id': False}):
        groups.append(group)
    return groups

def getProxys():
    """
    Get all Proxys from the Database
    """
    proxys = {}
    for proxy in client["proxys"].find({},{'_id': False}):
        proxys[proxy["name"]] = proxy["proxys"]
    return proxys


def getSettings():
    """
    Get the Settings from the Database
    """
    return client["settings"].find_one({},{'_id': False})


def Connect():
    """
    Connect Database
    """
    global client
    try:
        client = MongoClient(os.environ['DB'])["monitorsolutions"]
    except Exception as e:
        print(f"[DATABASE] Exception found: {traceback.format_exc()}")
        time.sleep(10)
        Connect()


#Connect Database when the Script is imported
Connect()


