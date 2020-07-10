from exceptions import RequestsException
from bs4 import BeautifulSoup
import requests
from constants import APP_NAME, BASE_URL


class liquipediapy():
    def __init__(self, game):
        self.game = game
        self.__headers = {'User-Agent': APP_NAME, 'Accept-Encoding': 'gzip'}
        self.__base_url = BASE_URL + '/' + game + '/api.php?'

    def parse(self, page):
        url = self.__base_url + 'action=parse&format=json&page=' + page
        response = requests.get(url, headers=self.__headers)
        if response.status_code == 200:
            try:
                page_html = response.json()['parse']['text']['*']
            except KeyError:
                raise ex.RequestsException(response.json(), response.status_code)
            soup = BeautifulSoup(page_html, features="lxml")
            redirect = soup.find('ul', class_="redirectText")
            if redirect is None:
                return soup, None
            else:
                redirect_value = soup.find('a').get_text()
                redirect_value = quote(redirect_value)
                soup, __ = self.parse(redirect_value)
                return soup, redirect_value
        else:
            raise RequestsException(response.json(), response.status_code)
