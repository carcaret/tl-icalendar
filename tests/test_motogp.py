from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from icalendar import Calendar

from sources import motogp
from sources.motogp import (build, normalize_session_code, season_years,
                            transform_events)


def upstream_event(code, gp, uid, start='20260913T120000Z'):
    return (
        'BEGIN:VEVENT\r\n'
        'DTSTAMP:20260825T100300Z\r\n'
        'DESCRIPTION:Round: GRAND PRIX\\nCategory: MotoGP\\nSession: Whatever\r\n'
        'DTSTART:{start}\r\n'
        'DTEND:20260913T124500Z\r\n'
        'LOCATION:Misano World Circuit\r\n'
        'SUMMARY:[MotoGP] {code} #{gp}\r\n'
        'UID:{uid}\r\n'
        'URL:https://www.motogp.com/en/calendar/2026/event/misano\r\n'
        'END:VEVENT\r\n'
    ).format(code=code, gp=gp, uid=uid, start=start)


def upstream_calendar(*events):
    return (
        'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:ICALENDAR-RS\r\n'
        + ''.join(events)
        + 'END:VCALENDAR\r\n'
    )


# Mirrors the real file: Q1/Q2/SPR/RAC per round, with Catalunya's race
# mislabelled as RAC2.
UPSTREAM = upstream_calendar(
    upstream_event('Q1', 'SanMarinoGP', 'uid-q1'),
    upstream_event('Q2', 'SanMarinoGP', 'uid-q2'),
    upstream_event('SPR', 'SanMarinoGP', 'uid-spr'),
    upstream_event('RAC', 'SanMarinoGP', 'uid-rac'),
    upstream_event('RAC2', 'CatalanGP', 'uid-rac2'),
)


@pytest.fixture
def events():
    return transform_events(UPSTREAM)


def summaries(events):
    return [str(event['summary']) for event in events]


def test_discards_q1(events):
    assert 'uid-q1' not in [str(event['uid']) for event in events]
    assert not any('Q1' in summary for summary in summaries(events))


def test_keeps_qualifying_sprint_and_races(events):
    assert summaries(events) == [
        '🏍 Clasificación — San Marino',
        '🏍 Sprint — San Marino',
        '🏍 Carrera — San Marino',
        '🏍 Carrera — Catalunya',
    ]


def test_numbered_race_code_survives_the_filter(events):
    assert 'uid-rac2' in [str(event['uid']) for event in events]


def test_numbered_race_code_is_normalized(events):
    rac2 = [e for e in events if str(e['uid']) == 'uid-rac2'][0]
    assert str(rac2['summary']) == '🏍 Carrera — Catalunya'


def test_normalize_session_code_only_touches_races():
    assert normalize_session_code('RAC2') == 'RAC'
    assert normalize_session_code('RAC7') == 'RAC'
    assert normalize_session_code('RAC') == 'RAC'
    assert normalize_session_code('Q1') == 'Q1'
    assert normalize_session_code('Q2') == 'Q2'
    assert normalize_session_code('SPR') == 'SPR'


def test_injects_two_display_alarms(events):
    for event in events:
        alarms = list(event.walk('VALARM'))
        assert len(alarms) == 2
        assert [str(alarm['action']) for alarm in alarms] == [
            'DISPLAY', 'DISPLAY']
        assert [alarm['trigger'].dt for alarm in alarms] == [
            timedelta(minutes=-60), timedelta(minutes=-10)]


def test_alarm_triggers_are_serialized_as_relative_durations(events):
    serialized = events[0].to_ical().decode()
    assert 'TRIGGER:-PT1H' in serialized
    assert 'TRIGGER:-PT10M' in serialized


def test_alarm_description_is_the_rewritten_summary(events):
    for event in events:
        for alarm in event.walk('VALARM'):
            assert str(alarm['description']) == str(event['summary'])


def test_uid_is_preserved(events):
    assert [str(event['uid']) for event in events] == [
        'uid-q2', 'uid-spr', 'uid-rac', 'uid-rac2']


def test_upstream_fields_are_preserved(events):
    event = events[0]
    assert event['dtstart'].dt == datetime(
        2026, 9, 13, 12, 0, tzinfo=timezone.utc)
    assert event['dtend'].dt == datetime(
        2026, 9, 13, 12, 45, tzinfo=timezone.utc)
    assert str(event['location']) == 'Misano World Circuit'
    assert str(event['url']).startswith('https://www.motogp.com/')
    assert 'Category: MotoGP' in str(event['description'])


def test_unknown_gp_tag_falls_back_to_the_tag_itself():
    events = transform_events(upstream_calendar(
        upstream_event('RAC', 'NewPlaceGP', 'uid-new')))
    assert str(events[0]['summary']) == '🏍 Carrera — New Place'


def test_unrecognized_summary_is_skipped():
    events = transform_events(upstream_calendar(
        'BEGIN:VEVENT\r\nUID:uid-odd\r\nSUMMARY:Some other thing\r\n'
        'DTSTART:20260913T120000Z\r\nEND:VEVENT\r\n',
        upstream_event('RAC', 'SanMarinoGP', 'uid-rac'),
    ))
    assert [str(event['uid']) for event in events] == ['uid-rac']


def test_season_years_is_the_current_year_during_the_season():
    assert season_years(date(2026, 9, 12)) == [2026]
    assert season_years(date(2026, 1, 5)) == [2026]


def test_season_years_adds_next_season_at_the_year_end():
    assert season_years(date(2026, 11, 1)) == [2026, 2027]
    assert season_years(date(2026, 12, 31)) == [2026, 2027]


def test_build_sets_calendar_metadata():
    with patch.object(motogp, 'fetch_season', return_value=UPSTREAM):
        calendar = build()

    assert isinstance(calendar, Calendar)
    assert str(calendar['x-wr-calname']) == 'MotoGP'
    assert calendar['refresh-interval'].dt == timedelta(hours=12)
    assert len(calendar.walk('VEVENT')) == 4


def test_build_merges_every_published_season():
    seasons = {
        2026: UPSTREAM,
        2027: upstream_calendar(
            upstream_event('RAC', 'ThaiGP', 'uid-2027', '20270228T080000Z')),
    }
    with patch.object(motogp, 'season_years', return_value=[2026, 2027]), \
            patch.object(motogp, 'fetch_season',
                         side_effect=lambda year, required=True: seasons[year]):
        calendar = build()

    uids = [str(event['uid']) for event in calendar.walk('VEVENT')]
    assert 'uid-2027' in uids
    assert len(uids) == 5


def test_build_tolerates_an_unpublished_next_season():
    responses = {
        2026: Mock(status_code=200, text=UPSTREAM,
                   raise_for_status=Mock()),
        2027: Mock(status_code=404),
    }
    with patch.object(motogp, 'season_years', return_value=[2026, 2027]), \
            patch.object(motogp.requests, 'get',
                         side_effect=lambda url, **kw: responses[
                             2027 if '2027' in url else 2026]):
        calendar = build()

    assert len(calendar.walk('VEVENT')) == 4


def test_build_fails_instead_of_publishing_an_empty_calendar():
    with patch.object(motogp, 'fetch_season',
                      return_value=upstream_calendar()):
        with pytest.raises(RuntimeError):
            build()
