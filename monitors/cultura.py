from threading import Thread
from datetime import datetime
from twocaptcha import TwoCaptcha
import random
import requests as rq
import time
import json
import logging
import traceback
import urllib3

class cultura:
    def __init__(self,groups,user_agents,delay=45,querys=[],blacksku=[],proxys=[]):
        self.user_agents = user_agents

        self.groups = groups
        self.delay = delay
        self.querys= querys
        self.proxys = proxys
        self.blacksku = blacksku
        self.proxytime = 0

        self.stores = {'CGN': 'Agen', 'CAM': 'Amiens', 'CAG': 'Anglet', 'CAB': 'Aubagne', 'CAU': 'Aubière', 'CAX': 'Auxerre', 'CBP': 'Bagnolet', 'CBM': 'Balma', 'CBA': 'Barentin', 'CB2': 'Bay 2-Collégien', 'CBY': 'Bayonne', 'CBU': 'Beauvais', 'CBG': 'Bègles', 'CBE': 'Belle Epine', 'CBC': 'Besançon', 'CBZ': 'Béziers', 'CBX': 'Bordeaux Lac', 'CBB': 'Bourg En Bresse', 'CBO': 'Bourgoin Jallieu', 'CBT': 'Brest', 'CBV': 'Brive Centre', 'CBR': 'Brive La Gaillarde', 'CMD': 'Caen Mondeville', 'CCR': 'Carcassonne', 'CCE': 'Carré Senart', 'CCT': 'Chambray Les Tours', 'CDO': "Champagne Au Mont d'Or", 'CC2': 'Champniers', 'CRE': 'Chantepie', 'CCP': 'Chasseneuil Du Poitou', 'CHO': 'Cholet', 'CCS': 'Claye Souilly', 'CRM': 'Cormontreuil', 'CDI': 'Dijon', 'CEY': 'Epagny', 'CEP': 'Epinal', 'CEV': 'Evreux', 'CFE': 'Fenouillet', 'CBN': 'Fouquieres Les Bethune', 'CFR': 'Franconville', 'CGM': 'Geispolsheim', 'CGE': 'Gennevilliers', 'CGI': 'Givors', 'CHB': 'Hénin-Beaumont', 'C4T': 'La Défense', 'CLT': 'La Teste', 'CLV': 'La Valentine', 'CLA': 'Labège', 'CLG': 'Langueux', 'CLM': 'Le Mans', 'CLE': 'Lescar', 'CLI': 'Limoges', 'CMA': 'Mâcon', 'CCA': 'Mandelieu', 'CMS': 'Marsac', 'CME': 'Mérignac', 'CMM': 'Metz', 'CMT': 'Montauban', 'CLH': 'Montivilliers', 'CML': 'Montluçon', 'CMU': 'Mundolsheim', 'CNB': 'Narbonne', 'CRQ': 'Neuville-en-Ferrain', 'CNC': 'Nice', 'CNI': 'Nîmes', 'COR': 'Pince Vent', 'CPL': 'Les Clayes-sous-Bois', 'CPC': 'Plan De Campagne', 'CPO': 'Portet Sur Garonne', 'CPB': 'Publier', 'CPT': 'Puget', 'CP2': 'Puilboreau', 'CRB': 'Rambouillet', 'CRV': 'Rivesaltes', 'CSA': 'Saint Aunès', 'CSB': 'Saint Berthevin', 'CS2': 'Saint Doulchard', 'CGR': 'Saint Grégoire', 'CSM': 'Saint Malo', 'CMR': 'Saint Maur', 'CCL': 'Saint Maximin', 'CSQ': 'Saint Quentin Fayet', 'CGV': 'Geneviève Des Bois', 'CSR': 'Saran', 'CLP': 'Sorgues', 'CTE': 'Terville', 'CTL': 'Toulon', 'CTN': 'Tours', 'CTR': 'Trignac', 'CTO': 'Troyes - St Parres', 'CVA': 'Valence', 'CCO': 'Venette', 'CAN': 'Ville-la-Grand', 'CVF': 'Villefranche', 'CV2': "Villeneuve D'Ascq", 'CVS': 'Villennes Sur Seine', 'CWM': 'Wittenheim'}

        self.session = rq.Session()
        self.INSTOCK = []
        
    def discord_webhook(self,group,title,sku,ean, url, thumbnail,prize,status, stores):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "cultura" not in group:
            return

        fields = []
        fields.append({"name": "Prize", "value": f"```{prize} €```", "inline": True})
        fields.append({"name": "SKU", "value": f"```{sku}```", "inline": True})
        fields.append({"name": "Total Instore Stock", "value": f"```{sum(s['qty'] for s in stores)}```", "inline": True})
        fields.append({"name": "Online-Status", "value": f"```{status}```", "inline": False})

        if len(stores)!=0:
            storenames = "\n"
            stock = ""
            for store in stores:
                storenames+=f"{self.stores[store['seller_code']]}\n"
                if store['qty']>3:
                    stock+=f"🟢 {store['qty']}\n"
                elif store['qty']==1:
                    stock+=f"🔴 {store['qty']}\n"
                else:
                    stock+=f"🟡 {store['qty']}\n"
                if len(storenames) > 970 or len(stock) > 970:
                    storenames+=f"....."
                    stock+=f"....."
                    break
            fields.append({"name": "Store", "value": f"```{storenames}```", "inline": True})
            fields.append({"name": "Stock", "value": f"```{stock}```", "inline": True})
            fields.append({"name": "🛒", "value": f"[ATC](https://cultura-eresa.onestock-retail.com/?products=&productID={ean}&itemID={ean})", "inline": False})

        data = {
            "username": group["Name"],
            "avatar_url": group["Avatar_Url"],
            "embeds": [{
            "title": title,
            "url": url, 
            "thumbnail": {"url": thumbnail},
            "fields": fields,
            "color": int(group['Colour']),
            "footer": {
                "text": f"{group['Name']} | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                "icon_url": group["Avatar_Url"]
                },
            "author": {
                "name": "Cultura"
            }
            }]
        }
        
        
        result = rq.post(group["cultura"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[cultura] Exception found: {err}")
        else:
            logging.info(msg=f'[cultura] Successfully sent Discord notification to {group["cultura"]}')
            print(f'[cultura] Successfully sent Discord notification to {group["cultura"]}')

    
    def solveCaptcha(self,response: rq.Response): 
        URL = f"https://geo.captcha-delivery.com/captcha/?initialCid={response.headers.get('x-datadome-cid')}&hash=0E1A81F31853AE662CAEC39D1CD529&cid={response.cookies.get('datadome')}&t=fe&referer={response.url}&s=11861"

        #Solve Captcha
        solver = TwoCaptcha('c1ff25bcdb98a045388b7587354d9d38')
        g_response = solver.recaptcha(sitekey="6LcSzk8bAAAAAOTkPCjprgWDMPzo_kgGC3E5Vn-T", url=URL)

        #SUBMIT CAPTCHA
        headers = {
        'Accept': '*/*',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': URL,
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'user-agent': response.request.headers.get("user-agent"),
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        }

        response = self.session.get(f"https://geo.captcha-delivery.com/captcha/check?cid={response.cookies.get('datadome')}&icid={response.headers.get('x-datadome-cid')}&ccid=&g-recaptcha-response={g_response['code']}&hash=0E1A81F31853AE662CAEC39D1CD529&ua={response.request.headers.get('user-agent')}&referer={response.url}&parent_url=https%3A%2F%2Fwww.cultura.com%2F&x-forwarded-for=&captchaChallenge=184826891&s=11861", headers=headers)
        response.raise_for_status()
        cookie = response.json()["cookie"]
        self.session.cookies.set("datadome", cookie[cookie.find("=")+1:cookie.find(";")])
        logging.info(msg=f'[cultura] Successfully solved Captcha and got a new Datadome Cookie')


    def scrape_site(self,query,headers, proxy):
        """
        Scrapes the specified cultura query site and adds items to array
        """
        items = []

        # Makes request to site
        output = []
        page = 1
        lastpage = 2
        while page != lastpage and lastpage != 0:
            html = self.session.get('https://www.cultura.com/magento/graphql?query={products(currentPage%3A'+str(page)+'%2CpageSize%3A200%2Csearch%3A%22'+query+'%22%2CresolverLight%3A1){total_count,global_expanded_facets,aggregations{options{count,label,value},attribute_code,count,label,is_swatch,expanded_mode},page_info{category{label,value},color_affiliation{label,value},seller_name%20{label,value},page_size,current_page,total_pages,__typename},items%20{__typename,id,sku,name,image{name,url},small_image{url},url_key,type_id,cross_format,cross_format_label,ean,front_subtitle,automatic_flags,manual_flags,main_flag%20{label,value},gsm_salesrule_ids{gsm_salesrule_id,gsm_salesrule_title,gsm_salesrule_banner_title,gsm_salesrule_description,gsm_salesrule_picto,gsm_salesrule_url,gsm_salesrule_offer},price_range{minimum_price{regular_price%20{value,currency},final_price%20{value,currency},discount%20{amount_off,percent_off},final_price_excl_tax%20{value,currency}},maximum_price%20{regular_price%20{value,currency},final_price%20{value,currency},discount%20{amount_off,percent_off}}},...%20on%20ConfigurableProduct{price_range{maximum_price{regular_price%20{value,currency},final_price%20{value,currency},discount%20{amount_off,percent_off}}}},attribute_set_id,attribute_set_name,release_date,backorder_end_date,web_sellable,stock_item_extra{front_availability,availability_date,order_delay,min_quantity_in_cart,offer{availability,seller_code,qty}},book_support,support_musical_custom_:%20support_musical,support_video_custom_:%20support_video,format_book_custom_:%20format_book,button_id_custom_:%20button_id,special_price_custom_:%20special_price}}}', headers=headers, proxies=proxy, verify=False, timeout=10)
            if html.status_code == 403:
                self.solveCaptcha(html)
                html = self.session.get('https://www.cultura.com/magento/graphql?query={products(currentPage%3A'+str(page)+'%2CpageSize%3A200%2Csearch%3A%22'+query+'%22%2CresolverLight%3A1){total_count,global_expanded_facets,aggregations{options{count,label,value},attribute_code,count,label,is_swatch,expanded_mode},page_info{category{label,value},color_affiliation{label,value},seller_name%20{label,value},page_size,current_page,total_pages,__typename},items%20{__typename,id,sku,name,image{name,url},small_image{url},url_key,type_id,cross_format,cross_format_label,ean,front_subtitle,automatic_flags,manual_flags,main_flag%20{label,value},gsm_salesrule_ids{gsm_salesrule_id,gsm_salesrule_title,gsm_salesrule_banner_title,gsm_salesrule_description,gsm_salesrule_picto,gsm_salesrule_url,gsm_salesrule_offer},price_range{minimum_price{regular_price%20{value,currency},final_price%20{value,currency},discount%20{amount_off,percent_off},final_price_excl_tax%20{value,currency}},maximum_price%20{regular_price%20{value,currency},final_price%20{value,currency},discount%20{amount_off,percent_off}}},...%20on%20ConfigurableProduct{price_range{maximum_price{regular_price%20{value,currency},final_price%20{value,currency},discount%20{amount_off,percent_off}}}},attribute_set_id,attribute_set_name,release_date,backorder_end_date,web_sellable,stock_item_extra{front_availability,availability_date,order_delay,min_quantity_in_cart,offer{availability,seller_code,qty}},book_support,support_musical_custom_:%20support_musical,support_video_custom_:%20support_video,format_book_custom_:%20format_book,button_id_custom_:%20button_id,special_price_custom_:%20special_price}}}', headers=headers, proxies=proxy, verify=False, timeout=10)
            html.raise_for_status()
            data = html.json()["data"]["products"]
            lastpage = data["page_info"]["total_pages"]
            if lastpage != data["page_info"]["current_page"]:
                page+=1
                time.sleep(7)
            for product in data["items"]:
                output.append(product)

        
        # Stores particular details in array
        for product in output:
            product_item = {
                'name': product['name'],
                'ean':product['ean'],
                'url': "https://www.cultura.com/p-"+product["url_key"]+".html",
                'image': "https://cdn.cultura.com/cdn-cgi/image/width=1024/"+str(product['image']['url']) if product['image']['url'] != None else "https://www.cultura.com/etc.clientlibs/cultura-one/clientlibs/clientlib-site/resources/images/placeholder.jpg", 
                'sku': product['sku'],
                'prize': product['price_range']['minimum_price']['final_price']['value'],
                'availability': product['stock_item_extra']['front_availability'],
                'stores': product['stock_item_extra']['offer']
                }
            items.append(product_item)
        
        logging.info(msg=f'[cultura] Successfully scraped Query {query}')
        return items

    def remove(self,sku):
        """
        Remove all Products from INSTOCK with the same sku
        """
        for elem in self.INSTOCK:
            if sku == elem[1]:
                self.INSTOCK.remove(elem)

    def updated(self,product):
        """
        Check if the stores or availability got updated
        """
        for elem in self.INSTOCK:
            #Check if Product was changed
            if product[1] == elem[1] and product[2] == elem[2]:
                if product[3] == elem[3]:
                    return [False,False]
                #Dont ping if no new store was added
                if len(product[3]) <= len(elem[3]):
                    if all(store in elem[3] for store in product[3]):
                        return [False,True]

            #Dont Ping when the Product goes OOS
            if product[1] == elem[1] and product[2] != elem[2] and product[2]=="unavailable":
                return [False,True]
        return[True,True]


    def comparitor(self,product, start):
        product_item = [product['name'], product['sku'], product['availability']]

        # Collect all available stores
        available_stores = []
        for store in product['stores']:
            if store['availability'] == "available": 
                available_stores.append(store["seller_code"])

        
        product_item.append(available_stores) # Appends in field
        
        
        ping, updated = self.updated(product_item)
        if updated or start == 1:
            # If product is available but not stored or product is stored but available stores are changed - sends notification and stores

            # Remove old version of the product
            self.remove(product_item[1])
            
            self.INSTOCK.append(product_item)
            if start == 0:
                print(f"[cultura] {product_item}")
                logging.info(msg=f"[cultura] {product_item}")

                if ping:
                    for group in self.groups:
                        #Send Ping to each Group
                        Thread(target=self.discord_webhook,args=(
                            group,
                            product["name"],
                            product['sku'],
                            product['ean'],
                            product['url'],
                            product['image'],
                            product['prize'],
                            product['availability'],
                            product['stores'],
                            )).start()
        

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/cultura.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING cultura MONITOR')
        logging.info(msg=f'cultura Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising proxy and headers
        proxy_no = -1
        headers = {
                'authority': 'www.cultura.com',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-language': 'de-DE,de;q=0.9',
                'cache-control': 'max-age=0',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': random.choice(self.user_agents)["user_agent"]
        }
        
        while True:
            try:
                #Rotate Proxys on each request
                proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}
                startTime = time.time()
                for query in self.querys:
                # Makes request to site and stores products 
                    items = self.scrape_site(query, headers, proxy)
                    for product in items:
                        if product["sku"] not in self.blacksku:
                            # Check if Item Status has changed
                            self.comparitor(product, start)
                    time.sleep(self.delay/len(self.querys))

                # Allows changes to be notified
                start = 0

                #Shuffle Query Order
                random.shuffle(self.querys)

                logging.info(msg=f'[cultura] Checked all querys in {time.time()-startTime} seconds')

            except Exception as e:
                print(f"[cultura] Exception found: {traceback.format_exc()}")
                logging.error(e)
                time.sleep(60)
                # Rotates headers
                headers["user-agent"] = random.choice(self.user_agents)["user_agent"]

                # Safe time to let the Monitor only use the Proxy for 60 min
                if proxy == {}:
                    self.proxytime = time.time()+3600
                
                if len(self.proxys) != 0:
                    # If optional proxy set, rotates if there are multiple proxies
                    proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                    proxy = {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}


if __name__ == '__main__':
    devgroup = {
        "Name":"Nabil DEV",
        "Avatar_Url":"https://i.imgur.com/H7rGtJ1.png",
        "Colour":1382451,
        "cultura":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    logging.basicConfig(filename=f'cultura.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)
    s = cultura(groups=[devgroup],user_agents=[{"user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36"}],querys=["spiderman no way home"])
    s.monitor()