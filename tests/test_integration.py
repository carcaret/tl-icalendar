"""
Integration tests — hit real external APIs, no mocks.
Run with: pytest tests/test_integration.py -v
"""
import pytest
from starcraft2 import get_s_tier_tournaments
from tl_icalendar import get_xml_calendar, parse_xml_calendar, CALENDAR_URL


@pytest.fixture(scope='module')
def s_tier_urls():
    return get_s_tier_tournaments()


@pytest.fixture(scope='module')
def calendar_events(s_tier_urls):
    xml = get_xml_calendar(CALENDAR_URL)
    return parse_xml_calendar(xml)


def test_s_tier_returns_non_empty_list(s_tier_urls):
    assert len(s_tier_urls) > 0


def test_s_tier_urls_are_liquipedia_sc2_urls(s_tier_urls):
    for url in s_tier_urls:
        assert url.startswith('https://liquipedia.net/starcraft2/')


def test_calendar_returns_events(calendar_events):
    assert len(calendar_events) > 0


def test_all_events_are_sc2(calendar_events):
    assert all(e['type'] == 'StarCraft 2' for e in calendar_events)


def test_no_replay_casts_in_events(calendar_events):
    assert all(e['title'] != 'Replay Cast' for e in calendar_events)


def test_all_events_have_required_fields(calendar_events):
    required = {'year', 'month', 'day', 'hour', 'minute', 'type', 'title', 'description', 'id', 'url'}
    for event in calendar_events:
        assert required <= event.keys()
        assert isinstance(event['year'], int)
        assert isinstance(event['month'], int)
        assert isinstance(event['day'], int)


def test_all_events_url_matches_a_s_tier_tournament(calendar_events, s_tier_urls):
    for event in calendar_events:
        assert any(t_url in event['url'] for t_url in s_tier_urls), (
            f"Event '{event['title']}' has URL '{event['url']}' not matching any S-Tier tournament"
        )
