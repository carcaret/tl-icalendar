from tl_api import liquipediapy
from constants import BASE_URL


class starcraft2():

    def __init__(self):
        self.liquipedia = liquipediapy('starcraft2')

    def get_s_tier_tournaments(self):
        soup, __ = self.liquipedia.parse('S-Tier_Tournaments')
        tournament_base_urls = []
        tournament_rows = soup.find_all('div', class_='gridRow')
        for row in tournament_rows:
            url = row.find('a').get('href')
            tournament_base_urls.append(BASE_URL + url)
        return tournament_base_urls
