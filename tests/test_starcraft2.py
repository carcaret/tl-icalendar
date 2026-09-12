from unittest.mock import Mock, patch

from icalendar import Calendar

from constants import LIQUIPEDIA_BASE_URL
from sources.starcraft2 import (create_icalendar, get_s_tier_tournaments,
                                parse_xml_calendar)

S_TIER_URL = LIQUIPEDIA_BASE_URL + \
    '/starcraft2/Global_StarCraft_II_League/2026/Season_1'

CALENDAR_XML = b"""
<calendar>
  <month year="2026" num="4">
    <day num="20">
      <event hour="10" minute="30">
        <type>StarCraft 2</type>
        <title>GSL Match</title>
        <description>Group Stage</description>
        <event-id>111</event-id>
        <liquipedia-url>https://liquipedia.net/starcraft2/Global_StarCraft_II_League/2026/Season_1</liquipedia-url>
      </event>
      <event hour="14" minute="0">
        <type>StarCraft 2</type>
        <title>Replay Cast</title>
        <description>Replay Cast description</description>
        <event-id>222</event-id>
        <liquipedia-url>https://liquipedia.net/starcraft2/Global_StarCraft_II_League/2026/Season_1</liquipedia-url>
      </event>
      <event hour="16" minute="0">
        <type>StarCraft 2</type>
        <title>A-Tier Match</title>
        <description>Some A-Tier tournament</description>
        <event-id>333</event-id>
        <liquipedia-url>https://liquipedia.net/starcraft2/RSL_Revival/Season_4</liquipedia-url>
      </event>
      <event hour="18" minute="0">
        <type>Warcraft III</type>
        <title>WC3 Match</title>
        <description>Not SC2</description>
        <event-id>444</event-id>
        <liquipedia-url>https://liquipedia.net/warcraft3/Some_Tournament</liquipedia-url>
      </event>
    </day>
  </month>
</calendar>
"""

CATEGORY_RESPONSE = {
    'query': {
        'categorymembers': [
            {'pageid': 1, 'ns': 0, 'title': 'Global StarCraft II League/2026/Season 1'},
            {'pageid': 2, 'ns': 0, 'title': 'HomeStory Cup/28'},
            {'pageid': 3, 'ns': 0, 'title': 'Esports World Cup/2025'},
        ]
    }
}

SC2_EVENT = {
    'year': 2026, 'month': 4, 'day': 20,
    'hour': 10, 'minute': 30,
    'type': 'StarCraft 2',
    'title': 'GSL Match',
    'description': 'Group Stage',
    'id': '111',
    'url': S_TIER_URL,
}


@patch('sources.starcraft2.get_s_tier_tournaments', return_value=[S_TIER_URL])
def test_includes_s_tier_sc2_events(mock_tournaments):
    events = parse_xml_calendar(CALENDAR_XML)
    assert len(events) == 1
    assert events[0]['id'] == '111'


@patch('sources.starcraft2.get_s_tier_tournaments', return_value=[S_TIER_URL])
def test_excludes_replay_casts(mock_tournaments):
    events = parse_xml_calendar(CALENDAR_XML)
    assert all(e['title'] != 'Replay Cast' for e in events)


@patch('sources.starcraft2.get_s_tier_tournaments', return_value=[S_TIER_URL])
def test_excludes_non_s_tier_events(mock_tournaments):
    events = parse_xml_calendar(CALENDAR_XML)
    assert all(e['id'] != '333' for e in events)


@patch('sources.starcraft2.get_s_tier_tournaments', return_value=[S_TIER_URL])
def test_excludes_non_sc2_events(mock_tournaments):
    events = parse_xml_calendar(CALENDAR_XML)
    assert all(e['type'] == 'StarCraft 2' for e in events)


@patch('sources.starcraft2.get_s_tier_tournaments', return_value=[S_TIER_URL])
def test_event_fields_are_parsed_correctly(mock_tournaments):
    events = parse_xml_calendar(CALENDAR_XML)
    assert events[0] == SC2_EVENT


def test_create_icalendar_returns_calendar_with_events():
    calendar = create_icalendar([SC2_EVENT], 'StarCraft 2')

    assert isinstance(calendar, Calendar)
    components = list(calendar.walk('VEVENT'))
    assert len(components) == 1
    assert str(components[0]['summary']) == 'GSL Match (StarCraft 2)'
    assert str(components[0]['uid']) == '111'


def test_create_icalendar_keeps_the_korean_timezone():
    calendar = create_icalendar([SC2_EVENT], 'StarCraft 2')
    dtstart = list(calendar.walk('VEVENT'))[0]['dtstart']

    assert dtstart.dt.tzinfo.key == 'Asia/Seoul'
    assert dtstart.dt.hour == 10 and dtstart.dt.minute == 30


def test_create_icalendar_skips_other_event_types():
    event = dict(SC2_EVENT, type='Warcraft III', id='999')
    calendar = create_icalendar([event], 'StarCraft 2')
    assert list(calendar.walk('VEVENT')) == []


@patch('sources.starcraft2.requests.get')
def test_returns_liquipedia_urls(mock_get):
    mock_get.return_value = Mock(json=lambda: CATEGORY_RESPONSE)

    assert get_s_tier_tournaments() == [
        LIQUIPEDIA_BASE_URL + '/starcraft2/Global_StarCraft_II_League/2026/Season_1',
        LIQUIPEDIA_BASE_URL + '/starcraft2/HomeStory_Cup/28',
        LIQUIPEDIA_BASE_URL + '/starcraft2/Esports_World_Cup/2025',
    ]


@patch('sources.starcraft2.requests.get')
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


@patch('sources.starcraft2.requests.get')
def test_returns_empty_list_when_no_tournaments(mock_get):
    mock_get.return_value = Mock(
        json=lambda: {'query': {'categorymembers': []}})

    assert get_s_tier_tournaments() == []
