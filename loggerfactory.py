import logging


def create(name, level=logging.DEBUG):
    """Factory function to create a logger"""

    handler = logging.FileHandler("logs/"+name+".log", mode="w")        
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))
    handler.setLevel(level)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

