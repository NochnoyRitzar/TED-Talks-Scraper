import requests
# import library for faster scraping
import cchardet
from bs4 import BeautifulSoup, SoupStrainer

from constants import TED_URL
from db_connect import client

# speed up program by filtering what to parse
catalog_parse_only = SoupStrainer('div', id='browse-results')
# page_parse_only = SoupStrainer('main', id='maincontent')
page_parse_only = SoupStrainer('script', id='__NEXT_DATA__')

# connect to 'talks_info' collection in 'TEDTalks' db
collection = client['TEDTalks']['talks_info']
session = requests.Session()


class WebScrappy:

    def __init__(self):
        self.talk_count = 0
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

    def scrape_catalog_page_info(self, catalog_page):
        """
        Get info about title, speaker, date posted, talk duration and talk page url from catalog page
        (https://www.ted.com/talks)

        :return: Return list of talks info
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

            talk_page_content = WebScrappy.get_talk_page(talk_page_url)

            talk_page_info = WebScrappy.scrape_talk_page_info(talk_page_content)

            # get talk duration and remove space in the beginning
            talk_duration = talk_image.a.span.contents[1].get_text(strip=True)
            title = talk_info.h4.find_next_sibling().a.get_text(strip=True)
            date_posted = talk_info.div.span.span.get_text(strip=True)

            data.append({'_id': self.talk_count,
                         'title': title,
                         'date': date_posted,
                         'duration': talk_duration,
                         'page_url': talk_page_url,
                         **talk_page_info})

            self.talk_count += 1

        return data

    @staticmethod
    def get_talk_page(talk_page_url):
        """

        :param talk_page_url: url of a talk's page
        :return: Return page html content
        """
        response = session.get(talk_page_url)
        talk_page = BeautifulSoup(response.content, 'lxml', parse_only=page_parse_only)
        return talk_page

    @staticmethod
    def scrape_talk_page_info(talk_page):
        """
        Get views, likes count, topics, summary, related videos, speakers info from a talk's page

        :param talk_page:
        :return: Talk information from it's page on TED
        :rtype: dict
        """
        


        # page_right_side = talk_page.find('aside')
        # # get topic list and iterate over it to get video topics
        # talk_topics_list = page_right_side.find('ul')
        # topics = [li.a.get_text(strip=True) for li in talk_topics_list.contents] if talk_topics_list else []
        # # iterate over 'related videos' and extract information about them
        # related_videos_section = page_right_side.find('div', attrs={'id': 'tabs--1--panel--0'}).select('a')
        # related_videos = [WebScrappy.scrape_related_video_info(video) for video in related_videos_section]
        #
        # page_left_side = page_right_side.previous_sibling
        # # find direct children of div element with class containing 'flex'
        # talk_stats, talk_summary, _ = page_left_side.contents[1].find_all(attrs={'class': 'flex'}, recursive=False)
        # views_and_event = talk_stats.div.div.get_text(strip=True).split(' ')
        # event = views_and_event[-1]
        # views = views_and_event[0].replace(',', '')
        # views = None if not views.isdigit() else int(views)
        # like_count = talk_stats.find('span').get_text(strip=True)[1:-1]
        # summary = talk_summary.find(attrs={'class': 'text-sm mb-6'}).get_text(strip=True)
        # # Talks can have either speakers or educators
        # # Scrape info from section (speakers or educators) that exists in a page
        # # If both sections don't exist set speakers list to empty
        # speakers_section = page_left_side.select('div.mr-2.w-14 + div')
        # educators_section = page_left_side.find_all('div', attrs={'class': 'mt-3 mb-6'})
        # if speakers_section:
        #     speakers_section = [div.contents for div in speakers_section]
        #     speakers = [
        #         {'name': div[0].get_text(),
        #          'occupation': div[1].get_text()} for div in speakers_section
        #     ]
        # elif educators_section:
        #     speakers = [
        #         {'name': div.previous_sibling.find('div', attrs={'class': 'text-base'}).get_text(),
        #          'occupation': 'Educator'} for div in educators_section
        #     ]
        # else:
        #     speakers = []
        #
        # return {'views': views,
        #         'event': event,
        #         'like_count': like_count,
        #         'summary': summary,
        #         'topics': topics,
        #         'speakers': speakers,
        #         'related_videos': related_videos}

    @staticmethod
    def scrape_related_video_info(video):
        """
        Extract url, duration, views, date, title, speakers for related video

        :param video: related video
        :return: Information about related video
        :rtype: dict
        """
        page_url = TED_URL + video['href']

        video_info = video.div
        duration = video_info.find('div', attrs={'class': 'text-xxs'}).get_text()
        views_and_date, title, speakers = [
            tag.get_text(strip=True) for tag in video_info.find('div', attrs={'class': 'ml-4'}).contents
        ]
        views, date = views_and_date.split(' views | ')

        return {
            'page_url': page_url,
            'duration': duration,
            'views': views,
            'date': date,
            'title': title,
            'speakers': speakers
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
