from threading import Thread

def run(function, **kwargs):
    Thread(target=function, kwargs=kwargs).start()