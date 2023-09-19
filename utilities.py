import os
import re
import logging

from constants import LOG_FILE_NAME


def create_logger():
    logger = logging.getLogger('WebScrappy')
    logger.setLevel(logging.DEBUG)
    log_format = logging.Formatter('%(levelname)s: %(asctime)s - %(message)s')
    handler = logging.FileHandler(filename=LOG_FILE_NAME, encoding='utf-8', mode='w')
    handler.setFormatter(log_format)
    logger.addHandler(handler)

    return logger


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

                    return int(last_scraped_catalog_page) + 1
            # if line with info wasn't found
            else:
                return 1
    else:
        return 1


def save_html_to_file(html_content, save_path):
    """

    :param html_content:
    :param save_path:
    :return:
    """
    with open(os.path.join('data', save_path), 'wb') as f:
        f.write(html_content)
