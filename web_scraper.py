import os
import random
import time
import requests
import json
# import library for faster scraping
import cchardet

from fake_useragent import UserAgent
from bs4 import BeautifulSoup, SoupStrainer
from constants import TED_URL, HEADERS
from utilities import create_logger, find_last_scraped_catalog_page, save_html_to_file

# speed up program by filtering what to parse
catalog_parse_only = SoupStrainer('div', id='browse-results')
talk_page_parse_only = SoupStrainer('main', id='maincontent')
talk_data_parse_only = SoupStrainer('script', id='__NEXT_DATA__')
last_scraped_page = find_last_scraped_catalog_page()
logger = create_logger()
ua = UserAgent()


class WebScrappy:

    def __init__(self):
        self.last_page = WebScrappy.get_pages_count()
        self.start_scraping()

    @staticmethod
    def get_pages_count():
        """
        Perform request to catalog page to extract pagination last page number

        :return: Return last page number
        :rtype: int
        """

        response = requests.get(TED_URL + '/talks', headers=HEADERS)
        if response.status_code != 200:
            logger.error(f'Scraping pagination number resulted in {response.status_code} code')
            logger.error(f'Printing page content: {response.content}')

        catalog_page = BeautifulSoup(response.content, 'lxml', parse_only=catalog_parse_only)

        gap_span = catalog_page.find('span', class_='pagination__item pagination__gap')
        last_page_num = gap_span.find_next_sibling().get_text()
        return int(last_page_num)

    @staticmethod
    def get_catalog_page(page_number):
        """

        :param page_number: catalog page number
        :return:
        """
        time.sleep(random.randint(10, 20))

        HEADERS['User-Agent'] = ua.random
        url = f'{TED_URL}/talks?page={page_number}?sort=oldest'

        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            logger.error(f'Scraping catalog page {page_number} resulted in {response.status_code} code')
            logger.error(f'Printing page content: {response.content}')

        save_html_to_file(response.content, os.path.join('scraped_catalog_pages', f'catalog_page_{page_number}'))
        catalog_page = BeautifulSoup(response.content, 'lxml', parse_only=catalog_parse_only)

        return catalog_page

    @staticmethod
    def get_talk_page(url):
        """
        Get talk's data and page html content

        :param url: url of a talk's page
        :return: Return talk data and page html content
        """
        time.sleep(random.randint(15, 20))

        HEADERS['User-Agent'] = ua.random
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            logger.error(f'Scraping talk page {url} resulted in {response.status_code} code')
            logger.error(f'Printing page content: {response.content}')

        filename = url.split('/')[-1]
        save_html_to_file(response.content, os.path.join('scraped_talk_pages', filename, '.html'))

        return response.content

    @staticmethod
    def parse_talk_transcript(transcript_data):
        """
        Join transcript string into a single text

        :param transcript_data: response content containing transcript data
        :return: transcript of a talk
        """
        transcript_data = transcript_data.get('translation')
        # check if talk has no transcript
        if not transcript_data:
            return ''
        paragraphs_list = transcript_data['paragraphs']
        text_list = []
        for paragraph in paragraphs_list:
            cues = paragraph.get('cues')
            paragraph_text = [cue.get('text').replace('\n', ' ') for cue in cues]
            text_list.append(' '.join(paragraph_text))

        transcript = ' '.join(text_list)

        return transcript

    @staticmethod
    def parse_talk_page_info(page_content):
        """
        Get all information about a talk from its html content

        :param page_content: talk page html content
        :return: Talk information from its page on TED
        :rtype: dict
        """
        # parse page section containing almost all talk data
        talk_page_data = BeautifulSoup(page_content, 'lxml', parse_only=talk_data_parse_only)
        # parse talk's page content
        talk_page_content = BeautifulSoup(page_content, 'lxml', parse_only=talk_page_parse_only)

        talk_page_data = json.loads(talk_page_data.script.get_text())
        page_right_side = talk_page_content.find('aside')

        video_data = talk_page_data['props']['pageProps']['videoData']
        player_data = json.loads(video_data['playerData'])

        event = player_data['event']

        talk_data = {
            '_id': video_data['id'],
            'title': video_data['title'],
            'duration': video_data['duration'],
            'views': video_data['viewedCount'],
            'likes': page_right_side.find_previous_sibling('div').select_one('i.icon-heart + span').get_text()[2:-1],
            'summary': video_data['description'],
            'event': event,
            'recorded_date': video_data['recordedOn'],
            'published_date': video_data['publishedAt'],
            'topics': [
                {'id': topic['id'], 'name': topic['name']} for topic in video_data['topics']['nodes']
            ],
            'speakers': [
                {
                    'name': ' '.join([speaker['firstname'], speaker['lastname']]).strip(),
                    'occupation': 'Educator' if event == 'TED-Ed' else speaker['description']
                } for speaker in video_data['speakers']['nodes']
            ],
            'subtitle_languages': [
                {
                    'name': language['languageName'],
                    'code': language['languageCode']
                } for language in player_data['languages']
            ],
            'youtube_video_code': player_data.get('external', {}).get('code'),
            'related_videos': [video['id'] for video in video_data['relatedVideos']],
            'transcript': WebScrappy.parse_talk_transcript(talk_page_data['props']['pageProps']['transcriptData'])
        }

        return talk_data

    @staticmethod
    def scrape_catalog_page_info(catalog_page):
        """
        Scrape talks page url from catalog page

        :return: Return list of talks with their info
        :rtype: list
        """
        data = []

        # find all talks divs
        talk_divs = catalog_page.find_all('div', class_='media media--sm-v')
        for div in talk_divs:
            # get direct children
            talk_image, talk_info = div.find_all(recursive=False)

            # get url of a TED talk page
            url = TED_URL + talk_image.a['href']
            page_content = WebScrappy.get_talk_page(url)

            talk_page_info = WebScrappy.parse_talk_page_info(page_content)

            data.append({**talk_page_info, 'page_url': url})
            logger.debug(f'Finished scraping talk - {talk_page_info.get("title")}')

        return data

    def start_scraping(self):
        print('Starting to web scrape')
        # iterate over all catalog pages
        for page_number in range(1, self.last_page + 1):
            catalog_page = WebScrappy.get_catalog_page(page_number)

            catalog_page_talks_info = self.scrape_catalog_page_info(catalog_page)

            logger.debug(f'Finished scraping page {page_number}/{self.last_page}')

        print('Finished scraping! :)')


if __name__ == '__main__':
    # start web scraping
    scrappy = WebScrappy()
