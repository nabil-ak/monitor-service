def adonis(site, link):
    return f"[Adonis](https://quicktask.adonisbots.com/quicktask/?site={site}&product={link})"

def koi(site, link):
    return f"[Koi](http://localhost:58912/protocol/quicktask?site={site}&monitorInput={link})"

def panaio(site, link):
    return f"[PanAIO](https://www.panaio.com/quicktask?site={site}&link={link})"

def loscobot(site, link):
    return f"[Losco](https://www.loscobot.eu/dashboard/WAIT?site={site}&url={link}&size=random)"

def cybersole(site=None, link=None):
    return f"[Cybersole](https://cybersole.io/dashboard/quicktask?input={link})"

def thunder(site, link):
    return f"[Thunder](http://localhost:3928/qt?site={site}&url={link})"

def storm(site, link):
    return f"[StormAIO](https://dashboard.storm-aio.com/dashboard?quicktask=true&store={site}&product={link})"

