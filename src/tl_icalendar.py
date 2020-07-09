import os
import xml.etree.ElementTree as ET
from datetime import datetime

import pytz
import requests
from icalendar import Calendar, Event
from slugify import slugify

from src.starcraft2 import starcraft2


CALENDAR_URL = 'http://www.teamliquid.net/calendar/xml/calendar.xml'
TIMEZONE = 'Asia/Seoul'  # Must match the timezone used in the XML calendar.
STATIC_ROOT = os.path.join('calendars')
BUCKET_NAME = 'tl-icalendar'
SC2_EVENT_TYPE = 'StarCraft 2'


def get_xml_calendar(url):
    response = requests.get(url)
    return response.content


def parse_xml_calendar(calendar):
    events = []
    premier_tournaments_urls = starcraft2().get_premier_tournaments()

    for month in ET.fromstring(calendar):
        for day in month:
            for event in day:
                try:
                    event_type = event.find('type').text
                except AttributeError:
                    event_type = 'N/A'

                if event_type != SC2_EVENT_TYPE:
                    continue

                try:
                    event_url = event.find('liquipedia-url').text
                except AttributeError:
                    event_url = 'N/A'

                if event_url not in premier_tournaments_urls:
                    continue

                event_year = month.attrib['year']
                event_month = month.attrib['num']
                event_day = day.attrib['num']
                event_hour = event.attrib['hour']
                event_minute = event.attrib['minute']

                try:
                    event_title = event.find('title').text
                except AttributeError:
                    event_title = 'N/A'

                try:
                    event_description = event.find('description').text
                except AttributeError:
                    event_description = 'N/A'

                try:
                    event_id = event.find('event-id').text
                except AttributeError:
                    event_id = 'N/A'

                events.append({
                    'year': int(event_year),
                    'month': int(event_month),
                    'day': int(event_day),
                    'hour': int(event_hour),
                    'minute': int(event_minute),
                    'type': event_type,
                    'title': event_title,
                    'description': event_description,
                    'id': event_id,
                    'url': event_url
                })

    return events


def create_icalendar(events, event_type):
    calendar = Calendar()
    calendar.add('prodid', '-//TeamLiquid.net//Events Calendar//')
    calendar.add('version', '2.0')

    for item in events:
        if event_type == item['type']:
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
                tzinfo=pytz.timezone(TIMEZONE))
            )

            calendar.add_component(event)

    return calendar


def write_icalendar_to_file(calendar, event_type):
    if not os.path.exists(STATIC_ROOT):
        os.makedirs(STATIC_ROOT)
    filename = os.path.join(STATIC_ROOT, slugify(event_type) + '.ics')
    f = open(filename, 'wb')
    f.write(calendar.to_ical())
    f.close()
    return f.name


def upload_calendars():
    import boto3
    s3 = boto3.resource('s3')

    for filename in os.listdir('../calendars/'):
        data = open('calendars/' + filename, 'rb')
        s3.Bucket(BUCKET_NAME).put_object(Key=filename, Body=data)


def run():
    print('Fetching calendar from', CALENDAR_URL, '...')
    xml_calendar = get_xml_calendar(CALENDAR_URL)

    print('Parsing XML calendar ...')
    events = parse_xml_calendar(xml_calendar)

    print('Creating `{}` iCalendar ...'.format(SC2_EVENT_TYPE))
    icalendar = create_icalendar(events, SC2_EVENT_TYPE)

    print('\tWriting iCalendar to file ...')
    f = write_icalendar_to_file(icalendar, SC2_EVENT_TYPE)

    print('\tDone. Check `{}`'.format(f))

    print('Uploading to S3 ...')
    #upload_calendars()

    print('GG')


if __name__ == '__main__':
    run()
