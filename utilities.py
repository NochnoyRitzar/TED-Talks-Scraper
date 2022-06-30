import logging
import os
import re

from constants import LOG_FILE_NAME


logger = logging.getLogger('WebScrappy')
logger.setLevel(logging.INFO)

log_format = logging.Formatter('%(levelname)s: %(asctime)s - %(message)s')
handler = logging.FileHandler(filename=LOG_FILE_NAME, encoding='utf-8', mode='w')
handler.setFormatter(log_format)
logger.addHandler(handler)


def find_last_scraped_catalog_page():
    """
    Parse log file to find line with information about last scraped catalog page.\n
    If no file or no such line found - return 1

    :return: last scraped catalog page number
    :rtype: int
    """
    if os.path.exists(LOG_FILE_NAME):
        with open(LOG_FILE_NAME, 'r') as log_file:
            lines = log_file.readlines()
            for line in reversed(lines):
                if line.rstrip('\n')[-3:].isdigit():
                    last_scraped_catalog_page = re.search(r'(\d+)/\d+$', line).group(1)

                    return int(last_scraped_catalog_page)
            # if line with info wasn't found
            else:
                return 1
    else:
        return 1
