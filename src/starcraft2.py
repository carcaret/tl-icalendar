from tl_api import liquipediapy
from constants import BASE_URL


class starcraft2():

    def __init__(self):
        self.liquipedia = liquipediapy('starcraft2')

    def get_premier_tournaments(self):
        soup, __ = self.liquipedia.parse('Premier_Tournaments')
        premier_tournaments_urls = []
        tables = soup.find_all('table', class_='wikitable')
        current_year = tables[0]
        rows = current_year.find_all('tr')[1:]
        for row in rows:
            cells = row.find_all('td')
            anchor = cells[2].find_all('a', href=True)[0]
            premier_tournaments_urls.append(BASE_URL + anchor['href'])
        return premier_tournaments_urls
