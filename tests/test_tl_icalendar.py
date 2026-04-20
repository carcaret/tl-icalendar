from unittest.mock import patch
from icalendar import Calendar
from tl_icalendar import parse_xml_calendar, create_icalendar


S_TIER_URL = 'https://liquipedia.net/starcraft2/Global_StarCraft_II_League/2026/Season_1'

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


@patch('tl_icalendar.get_s_tier_tournaments', return_value=[S_TIER_URL])
def test_includes_s_tier_sc2_events(mock_tournaments):
    events = parse_xml_calendar(CALENDAR_XML)
    assert len(events) == 1
    assert events[0]['id'] == '111'


@patch('tl_icalendar.get_s_tier_tournaments', return_value=[S_TIER_URL])
def test_excludes_replay_casts(mock_tournaments):
    events = parse_xml_calendar(CALENDAR_XML)
    assert all(e['title'] != 'Replay Cast' for e in events)


@patch('tl_icalendar.get_s_tier_tournaments', return_value=[S_TIER_URL])
def test_excludes_non_s_tier_events(mock_tournaments):
    events = parse_xml_calendar(CALENDAR_XML)
    assert all(e['id'] != '333' for e in events)


@patch('tl_icalendar.get_s_tier_tournaments', return_value=[S_TIER_URL])
def test_excludes_non_sc2_events(mock_tournaments):
    events = parse_xml_calendar(CALENDAR_XML)
    assert all(e['type'] == 'StarCraft 2' for e in events)


@patch('tl_icalendar.get_s_tier_tournaments', return_value=[S_TIER_URL])
def test_event_fields_are_parsed_correctly(mock_tournaments):
    events = parse_xml_calendar(CALENDAR_XML)
    event = events[0]
    assert event == {
        'year': 2026, 'month': 4, 'day': 20,
        'hour': 10, 'minute': 30,
        'type': 'StarCraft 2',
        'title': 'GSL Match',
        'description': 'Group Stage',
        'id': '111',
        'url': S_TIER_URL,
    }


def test_create_icalendar_returns_calendar_with_events():
    events = [
        {
            'year': 2026, 'month': 4, 'day': 20,
            'hour': 10, 'minute': 30,
            'type': 'StarCraft 2',
            'title': 'GSL Match',
            'description': 'Group Stage',
            'id': '111',
            'url': S_TIER_URL,
        }
    ]
    calendar = create_icalendar(events, 'StarCraft 2')

    assert isinstance(calendar, Calendar)
    components = list(calendar.walk('VEVENT'))
    assert len(components) == 1
    assert str(components[0]['summary']) == 'GSL Match (StarCraft 2)'
    assert str(components[0]['uid']) == '111'


def test_create_icalendar_skips_other_event_types():
    events = [
        {
            'year': 2026, 'month': 4, 'day': 20,
            'hour': 10, 'minute': 0,
            'type': 'Warcraft III',
            'title': 'WC3 Match',
            'description': 'desc',
            'id': '999',
            'url': 'https://liquipedia.net/warcraft3/foo',
        }
    ]
    calendar = create_icalendar(events, 'StarCraft 2')
    assert list(calendar.walk('VEVENT')) == []
