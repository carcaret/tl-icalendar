import requests
from constants import APP_NAME, BASE_URL


def get_s_tier_tournaments():
    response = requests.get(
        BASE_URL + '/starcraft2/api.php',
        params={
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': 'Category:S-Tier_Tournaments',
            'cmlimit': '50',
            'cmsort': 'timestamp',
            'cmdir': 'desc',
            'format': 'json',
        },
        headers={'User-Agent': APP_NAME, 'Accept-Encoding': 'gzip'},
    )
    members = response.json()['query']['categorymembers']
    return [
        BASE_URL + '/starcraft2/' + m['title'].replace(' ', '_')
        for m in members
    ]
