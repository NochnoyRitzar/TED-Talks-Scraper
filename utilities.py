import logging


logger = logging.getLogger('WebScrappy')
logger.setLevel(logging.INFO)

format = logging.Formatter('%(levelname)s: %(asctime)s - [%(filename)s - %(lineno)s] - %(message)s')
handler = logging.FileHandler(filename='scraping.log', encoding='utf-8', mode='w')
handler.setFormatter(format)
logger.addHandler(handler)
