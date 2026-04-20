from unittest.mock import patch, Mock
from starcraft2 import get_s_tier_tournaments
from constants import BASE_URL


CATEGORY_RESPONSE = {
    'query': {
        'categorymembers': [
            {'pageid': 1, 'ns': 0, 'title': 'Global StarCraft II League/2026/Season 1'},
            {'pageid': 2, 'ns': 0, 'title': 'HomeStory Cup/28'},
            {'pageid': 3, 'ns': 0, 'title': 'Esports World Cup/2025'},
        ]
    }
}


@patch('starcraft2.requests.get')
def test_returns_liquipedia_urls(mock_get):
    mock_get.return_value = Mock(json=lambda: CATEGORY_RESPONSE)

    urls = get_s_tier_tournaments()

    assert urls == [
        BASE_URL + '/starcraft2/Global_StarCraft_II_League/2026/Season_1',
        BASE_URL + '/starcraft2/HomeStory_Cup/28',
        BASE_URL + '/starcraft2/Esports_World_Cup/2025',
    ]


@patch('starcraft2.requests.get')
def test_calls_category_api_with_correct_params(mock_get):
    mock_get.return_value = Mock(json=lambda: CATEGORY_RESPONSE)

    get_s_tier_tournaments()

    _, kwargs = mock_get.call_args
    params = kwargs['params']
    assert params['action'] == 'query'
    assert params['list'] == 'categorymembers'
    assert params['cmtitle'] == 'Category:S-Tier_Tournaments'
    assert params['cmsort'] == 'timestamp'
    assert params['cmdir'] == 'desc'


@patch('starcraft2.requests.get')
def test_returns_empty_list_when_no_tournaments(mock_get):
    mock_get.return_value = Mock(json=lambda: {'query': {'categorymembers': []}})

    assert get_s_tier_tournaments() == []
