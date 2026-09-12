"""StarCraft 2 calendar, built from TeamLiquid's XML calendar.

Unlike the MotoGP source, which transforms an existing ICS, here the events are
constructed from scratch: TeamLiquid publishes an XML calendar of every event,
which we cross-check against Liquipedia's S-Tier tournament category so only
the premier tournaments make it in.
"""
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from icalendar import Calendar, Event

from constants import APP_NAME, LIQUIPEDIA_BASE_URL

CALENDAR_URL = 'http://www.teamliquid.net/calendar/xml/calendar.xml'
TIMEZONE = ZoneInfo('Asia/Seoul')  # Matches the timezone used in the XML.
EVENT_TYPE = 'StarCraft 2'
EXCLUDED_TITLES = ('Replay Cast',)

CALENDAR_NAME = 'StarCraft 2 (S-Tier)'
PRODID = '-//TeamLiquid.net//Events Calendar//'


def get_s_tier_tournaments():
    """Liquipedia pages of the current S-Tier tournaments."""
    response = requests.get(
        LIQUIPEDIA_BASE_URL + '/starcraft2/api.php',
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
        timeout=20,
    )
    members = response.json()['query']['categorymembers']
    return [
        LIQUIPEDIA_BASE_URL + '/starcraft2/' + m['title'].replace(' ', '_')
        for m in members
    ]


def get_xml_calendar(url):
    response = requests.get(url, headers={'User-Agent': APP_NAME}, timeout=20)
    return response.content


def _text(event, tag):
    try:
        return event.find(tag).text
    except AttributeError:
        return 'N/A'


def parse_xml_calendar(calendar):
    events = []
    s_tier_tournaments_base_urls = get_s_tier_tournaments()

    for month in ET.fromstring(calendar):
        for day in month:
            for event in day:
                event_type = _text(event, 'type')
                if event_type != EVENT_TYPE:
                    continue

                event_url = _text(event, 'liquipedia-url')
                if not any(tournament_url in event_url
                           for tournament_url in s_tier_tournaments_base_urls):
                    continue

                event_title = _text(event, 'title')
                if event_title in EXCLUDED_TITLES:
                    continue

                events.append({
                    'year': int(month.attrib['year']),
                    'month': int(month.attrib['num']),
                    'day': int(day.attrib['num']),
                    'hour': int(event.attrib['hour']),
                    'minute': int(event.attrib['minute']),
                    'type': event_type,
                    'title': event_title,
                    'description': _text(event, 'description'),
                    'id': _text(event, 'event-id'),
                    'url': event_url,
                })
    return events


def create_icalendar(events, event_type):
    calendar = Calendar()
    calendar.add('prodid', PRODID)
    calendar.add('version', '2.0')
    calendar.add('x-wr-calname', CALENDAR_NAME)

    for item in events:
        if event_type != item['type']:
            continue

        event = Event()
        event.add('summary', '{} ({})'.format(item['title'], item['type']))
        event.add('description', '{}\nLiquipedia: {}'.format(
            item['description'], item['url']))
        event.add('uid', item['id'])
        event.add('dtstart', datetime(
            item['year'],
            item['month'],
            item['day'],
            item['hour'],
            item['minute'],
            0,  # Seconds.
            tzinfo=TIMEZONE,
        ))

        calendar.add_component(event)

    return calendar


def build():
    print('\tFetching {} ...'.format(CALENDAR_URL))
    events = parse_xml_calendar(get_xml_calendar(CALENDAR_URL))
    return create_icalendar(events, EVENT_TYPE)
