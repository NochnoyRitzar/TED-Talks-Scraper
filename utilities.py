import logging


logger = logging.getLogger('WebScrappy')
logger.setLevel(logging.INFO)

log_format = logging.Formatter('%(levelname)s: %(asctime)s - %(message)s')
handler = logging.FileHandler(filename='scraping.log', encoding='utf-8', mode='w')
handler.setFormatter(log_format)
logger.addHandler(handler)
