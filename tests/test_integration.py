"""
Integration tests — hit real external APIs, no mocks.
Run with: pytest tests/test_integration.py -v
"""
import pytest

from sources.motogp import (ALARM_OFFSETS, KEPT_SESSION_CODES, SOURCE_URL,
                            fetch_season, season_years, transform_events)
from sources.starcraft2 import (CALENDAR_URL, get_s_tier_tournaments,
                                get_xml_calendar, parse_xml_calendar)


@pytest.fixture(scope='module')
def s_tier_urls():
    return get_s_tier_tournaments()


@pytest.fixture(scope='module')
def calendar_events(s_tier_urls):
    xml = get_xml_calendar(CALENDAR_URL)
    return parse_xml_calendar(xml)


@pytest.fixture(scope='module')
def motogp_events():
    return transform_events(fetch_season(season_years()[0]))


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
    required = {'year', 'month', 'day', 'hour', 'minute',
                'type', 'title', 'description', 'id', 'url'}
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


def test_motogp_source_is_available():
    assert fetch_season(season_years()[0]).startswith('BEGIN:VCALENDAR')


def test_motogp_keeps_three_sessions_per_round(motogp_events):
    # Qualifying + sprint + race for every round of the season.
    assert len(motogp_events) % len(KEPT_SESSION_CODES) == 0
    assert len(motogp_events) >= 3


def test_motogp_drops_the_knock_out_qualifying(motogp_events):
    assert not any('Q1' in str(event['summary']) for event in motogp_events)


def test_motogp_summaries_are_rewritten(motogp_events):
    labels = ('Clasificación', 'Sprint', 'Carrera')
    for event in motogp_events:
        summary = str(event['summary'])
        assert summary.startswith('🏍 ')
        assert any(label in summary for label in labels)
        assert '#' not in summary and '[MotoGP]' not in summary


def test_motogp_every_event_has_both_alarms(motogp_events):
    for event in motogp_events:
        alarms = list(event.walk('VALARM'))
        assert len(alarms) == len(ALARM_OFFSETS)
        assert [alarm['trigger'].dt for alarm in alarms] == list(ALARM_OFFSETS)
        assert all(str(alarm['action']) == 'DISPLAY' for alarm in alarms)


def test_motogp_uids_are_upstream_and_unique(motogp_events):
    uids = [str(event['uid']) for event in motogp_events]
    assert len(set(uids)) == len(uids)
    assert all(uid.endswith('@codeberg.org_nixxo') for uid in uids)


def test_motogp_race_count_matches_round_count(motogp_events):
    races = [e for e in motogp_events if 'Carrera' in str(e['summary'])]
    rounds = {str(e['summary']).split('—')[1].strip() for e in motogp_events}
    assert len(races) == len(rounds)
