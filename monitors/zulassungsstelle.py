from multiprocessing import Process
from bs4 import BeautifulSoup
from proxymanager import ProxyManager
from user_agent import CHROME_USERAGENT
import requests as rq
import time
import json
import loggerfactory
import traceback
import urllib3
import webhook
import threadrunner

SITE = __name__.split(".")[1]

class zulassungsstelle(Process):
    def __init__(self, groups, settings):
        Process.__init__(self)
        self.groups = groups
        self.proxys = ProxyManager(settings["proxys"])
        self.delay = settings["delay"]
        self.firstScrape = True
        self.logger = loggerfactory.create(SITE)
        self.session = rq.Session()

        self.INSTOCK = []
        
    def discord_webhook(self, group, appointment):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """

        fields = []
        fields.append({"name": "Status", "value": f"**Neuer Termin**", "inline": True})
        
        webhook.send(group=group, webhook=group[SITE], site=f"{SITE}", title=appointment, url="https://tevis.ekom21.de/fra/select2?md=2", thumbnail="https://www.auto-data.net/images/f74/Volkswagen-Golf-VII-Variant.jpg", fields=fields, logger=self.logger)

    
    def gen_session(self):
        response = self.session.get("https://tevis.ekom21.de/fra/select2?md=2")
        response.raise_for_status()

    def scrape_site(self):
        appointments = []

        response = self.session.get("https://tevis.ekom21.de/fra/suggest?mdt=147&select_cnc=1&cnc-930=0&cnc-932=0&cnc-935=0&cnc-933=0&cnc-939=0&cnc-931=0&cnc-934=0&cnc-929=0&cnc-942=0&cnc-936=0&cnc-941=1&cnc-940=0&cnc-938=0&cnc-872=0&cnc-879=0&cnc-925=0")
        response.raise_for_status()

        output = BeautifulSoup(response.text, 'html.parser')
        app = output.find('div', {'id': 'sugg_accordion'}).find_all('h3')

        for appointment in app:
            appointments.append(appointment["title"])

        self.logger.info(msg=f'[{SITE}] Successfully scraped Appointments')
        return appointments
        

    def run(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        print(f'STARTING {SITE} MONITOR')
        
        while True:
            try:
                startTime = time.time()

                self.gen_session()
                appointments = self.scrape_site()

                for app in appointments:
                    if app not in self.INSTOCK and not self.firstScrape:
                        print(f"[{SITE}] {app} got restocked")
                        self.logger.info(msg=f"[{SITE}] {app} got restocked")
                        for group in self.groups:
                            #Send Ping to each Group
                            threadrunner.run(
                                self.discord_webhook,
                                group=group,
                                appointment=app
                            )
                    
                self.INSTOCK = appointments

                # Allows changes to be notified
                self.firstScrape = False

                self.logger.info(msg=f'[{SITE}] Checked appointments in {time.time()-startTime} seconds')
                self.session.cookies.clear()

                time.sleep(self.delay)

            except Exception as e:
                print(f"[{SITE}] Exception found: {traceback.format_exc()}")
                self.logger.error(e)
                time.sleep(5)