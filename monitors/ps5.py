import requests as rq
from datetime import datetime
import time
import json

def webhook(title,url):
    data = {
        "username": "PS5",
        "avatar_url": "https://media.direct.playstation.com/is/image/psdglobal/psLogo?$Icons$",
        "embeds": [{
            "title": title,
            "url": url, 
            "thumbnail": {"url": "https://www.pcgames.de/screenshots/1000x562/2021/09/PS5-kaufen-Playstation-5-bestellen-neues-Modell-pcgh5.jpg"},
            "color": 16777215,
            "timestamp": str(datetime.utcnow()),
        }]
    }
    response = rq.post("https://discord.com/api/webhooks/953814160511209503/vysO2UKZpKs3Whr6voSQaAehGQke2n1fuDunNk30Q4a96SC_z4f2WeTZdYvtXgXNm047", data=json.dumps(data), headers={"Content-Type": "application/json"})
    print(response.text)


while True:
    data = rq.get("https://api.direct.playstation.com/commercewebservices/ps-direct-de/users/anonymous/products/productList?fields=BASIC&lang=de_DE&productCodes=9710196-DE,9709091-DE",
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'}).json()
    instock = False
    for ps in data["products"]:
        print(str(ps["name"])+" --- "+(ps["stock"]["stockLevelStatus"]))
        if ps["stock"]["stockLevelStatus"] != "outOfStock":
            try:
                rq.get("http://api.callmebot.com/start.php?user=@xwe1010&text=PS5",timeout=15)
            except:
                pass
            if "Digital" in str(ps["name"]):
                webhook(str(ps["name"]),"https://direct.playstation.com/de-de/buy-consoles/playstation5-digital-edition-console")
            else:
                webhook(str(ps["name"]),"https://direct.playstation.com/de-de/buy-consoles/playstation5-console")
            instock = True
    if instock:
        break
    time.sleep(1)





