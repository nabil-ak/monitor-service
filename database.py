from pymongo import MongoClient
import logging
import traceback
import time

def getGroups():
    """
    Get all Cooking Groups from the Database
    """
    groups = []
    for group in client["groups"].find({},{'_id': False}):
        groups.append(group)
    return groups


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
        client = MongoClient("mongodb+srv://monitor:BfdiEzEhx1ZpXMgp@monitorsolutions.yerbc.mongodb.net/monitorsolutions?retryWrites=true&w=majority")["monitorsolutions"]
    except Exception as e:
        print(f"[DATABASE] Exception found: {traceback.format_exc()}")
        logging.error(e)
        time.sleep(10)
        Connect()


#Connect Database when the Script is imported
Connect()


