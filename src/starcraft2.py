from tl_api import liquipediapy


class starcraft2():

    def __init__(self):
        self.liquipedia = liquipediapy('starcraft2')

    def get_s_tier_tournaments(self):
        soup, __ = self.liquipedia.parse('S-Tier_Tournaments')
        tournament_titles = []
        tournament_rows = soup.find_all('div', class_='gridRow')
        for row in tournament_rows:
            title = row.find('a').get('title')
            tournament_titles.append(title)
        return tournament_titles
