import requests
import json
# import library for faster scraping
import cchardet
from bs4 import BeautifulSoup, SoupStrainer
from constants import TED_URL
from db_connect import client

# speed up program by filtering what to parse
catalog_parse_only = SoupStrainer('div', id='browse-results')
talk_page_parse_only = SoupStrainer('main', id='maincontent')
talk_data_parse_only = SoupStrainer('script', id='__NEXT_DATA__')

# connect to 'talks_info' collection in 'TEDTalks' db
collection = client['TEDTalks']['talks_info']
session = requests.Session()


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

        response = requests.get(TED_URL + '/talks')
        catalog_page = BeautifulSoup(response.content, 'lxml', parse_only=catalog_parse_only)

        gap_span = catalog_page.find('span', class_='pagination__item pagination__gap')
        last_page_num = gap_span.find_next_sibling().get_text()
        return int(last_page_num)

    @staticmethod
    def get_catalog_page(page_number):
        response = session.get(TED_URL + f'/talks?page={page_number}&sort=oldest')
        catalog_page = BeautifulSoup(response.content, 'lxml', parse_only=catalog_parse_only)

        return catalog_page

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
            talk_page_url = TED_URL + talk_image.a['href']

            talk_page_data, talk_page_content = WebScrappy.get_talk_page(talk_page_url)

            talk_page_info = WebScrappy.scrape_talk_page_info(talk_page_data, talk_page_content)

            data.append({**talk_page_info,
                         'page_url': talk_page_url})

        return data

    @staticmethod
    def get_talk_page(talk_page_url):
        """
        Get talk's data and page html content

        :param talk_page_url: url of a talk's page
        :return: Return talk data and page html content
        """
        response = session.get(talk_page_url)
        # parse page section containing almost all talk data
        talk_page_data = BeautifulSoup(response.content, 'lxml', parse_only=talk_data_parse_only)
        # parse talk's page content
        talk_page_content = BeautifulSoup(response.content, 'lxml', parse_only=talk_page_parse_only)
        return talk_page_data, talk_page_content

    @staticmethod
    def scrape_talk_page_info(talk_page_data, talk_page_content):
        """
        Get all information about a talk from it's data and html content

        :param talk_page_data: talk data
        :param talk_page_content: talk page html content
        :return: Talk information from it's page on TED
        :rtype: dict
        """
        talk_page_data = json.loads(talk_page_data.script.get_text())

        page_right_side = talk_page_content.find('aside')
        video_data = talk_page_data['props']['pageProps']['videoData']
        player_data = json.loads(video_data['playerData'])

        youtube_video_code = player_data.get('external').get('code')
        ted_id = video_data['id']
        title = video_data['title']
        views = video_data['viewedCount']
        duration = video_data['duration']
        recorded_date = video_data['recordedOn']
        published_date = video_data['publishedAt']
        summary = video_data['description']
        event = player_data['event']
        likes = page_right_side.find_previous_sibling('div').select_one('i.icon-heart + span').get_text()[2:-1]

        topics_list = [
            {'id': topic['id'], 'name': topic['name']} for topic in video_data['topics']['nodes']
        ]

        related_videos_list = [video['id'] for video in video_data['relatedVideos']]

        speakers_list = [
            {
                'name': ' '.join([speaker['firstname'], speaker['lastname']]).strip(),
                'occupation': 'Educator' if event == 'TED-Ed' else speaker['description']
            } for speaker in video_data['speakers']['nodes']
        ]

        languages_list = [
            {
                'name': language['languageName'],
                'code': language['languageCode']
            } for language in player_data['languages']
        ]

        return {
            '_id': ted_id,
            'title': title,
            'duration': duration,
            'views': views,
            'likes': likes,
            'summary': summary,
            'event': event,
            'recorded_date': recorded_date,
            'published_date': published_date,
            'topics': topics_list,
            'speakers': speakers_list,
            'subtitle_languages': languages_list,
            'youtube_video_code': youtube_video_code,
            'related_videos': related_videos_list
        }

    def start_scraping(self):
        print('Starting to web scrape')
        # iterate over all catalog pages
        for page_number in range(1, self.last_page + 1):
            print(f'Started scraping page {page_number}/{self.last_page}')
            catalog_page = WebScrappy.get_catalog_page(page_number)
            catalog_page_talks_info = self.scrape_catalog_page_info(catalog_page)
            print(f'Finished scraping page {page_number}/{self.last_page}')
            try:
                collection.insert_many(catalog_page_talks_info)
            except Exception as ex:
                print(ex)
        print('Finished scraping! :)')


if __name__ == '__main__':
    # start web scraping
    scrappy = WebScrappy()
