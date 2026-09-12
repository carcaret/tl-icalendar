"""MotoGP calendar, rebuilt from nixxo's upstream ICS.

The upstream file is usable but not subscribable as-is: it carries no alarms at
all and encodes the session in the SUMMARY as a code ("[MotoGP] SPR
#SanMarinoGP"). iOS shows the event SUMMARY in the notification (not the
VALARM DESCRIPTION), so we filter the sessions we care about, rewrite the
summaries in Spanish and inject the alarms ourselves.

UIDs are passed through untouched so upstream updates (session times move
around) are deduplicated by calendar clients instead of piling up.
"""
import re
from datetime import date, timedelta

import requests
from icalendar import Alarm, Calendar

from constants import APP_NAME

# Sessions kept in the calendar. Q1 is the knock-out session that starts 25
# minutes before Q2, so keeping it would only duplicate every warning. Change
# this one line to change the mix.
KEPT_SESSION_CODES = ('Q2', 'SPR', 'RAC')

# Injected on every surviving event. DISPLAY only: AUDIO and EMAIL support is
# patchy on iOS.
ALARM_OFFSETS = (timedelta(minutes=-60), timedelta(minutes=-10))

SOURCE_URL = ('https://nixxo.github.io/calendars/motogp/{year}/'
              'MotoGP_qualy-and-races_{year}_calendar.ics')

# The season matches the calendar year, so the year is derived from the clock
# instead of hardcoded. From this month on we also pull next season's file (if
# upstream already published it), which covers the turn of the year without a
# gap: the last race of a season is late November.
NEXT_SEASON_FROM_MONTH = 11

# Upstream summary, e.g. "[MotoGP] SPR #SanMarinoGP".
SUMMARY_PATTERN = re.compile(
    r'^\[(?P<series>[^\]]+)\]\s+(?P<code>\S+)\s+#(?P<gp>\S+)\s*$')

# Upstream erratum: the Catalunya race ships as RAC2 instead of RAC. Handled
# for any RACn so it keeps working wherever upstream slips next.
NUMBERED_RACE_CODE = re.compile(r'^RAC\d+$')

SESSION_LABELS = {
    'Q2': 'Clasificación',
    'SPR': 'Sprint',
    'RAC': 'Carrera',
}

GP_NAMES = {
    'ThaiGP': 'Tailandia',
    'BrasilGP': 'Brasil',
    'AmericasGP': 'Las Américas',
    'SpanishGP': 'España',
    'FrenchGP': 'Francia',
    'CatalanGP': 'Catalunya',
    'ItalianGP': 'Italia',
    'HungarianGP': 'Hungría',
    'CzechGP': 'Chequia',
    'DutchGP': 'Países Bajos',
    'GermanGP': 'Alemania',
    'BritishGP': 'Gran Bretaña',
    'AragonGP': 'Aragón',
    'SanMarinoGP': 'San Marino',
    'AustrianGP': 'Austria',
    'JapaneseGP': 'Japón',
    'IndonesianGP': 'Indonesia',
    'AustralianGP': 'Australia',
    'MalaysianGP': 'Malasia',
    'QatarGP': 'Catar',
    'PortugueseGP': 'Portugal',
    'ValenciaGP': 'Valencia',
}

CALENDAR_NAME = 'MotoGP'
PRODID = '-//carcaret//MotoGP Calendar//ES'
REFRESH_INTERVAL = timedelta(hours=12)


def season_years(today=None):
    """Seasons to pull, current first. Next season is added near the year end."""
    today = today or date.today()
    if today.month >= NEXT_SEASON_FROM_MONTH:
        return [today.year, today.year + 1]
    return [today.year]


def normalize_session_code(code):
    """RAC2 (and any RACn) is the Grand Prix race, mislabelled upstream."""
    if NUMBERED_RACE_CODE.match(code):
        return 'RAC'
    return code


def gp_name(tag):
    """`SanMarinoGP` -> `San Marino`. Unknown tags degrade, they don't break."""
    if tag in GP_NAMES:
        return GP_NAMES[tag]
    words = tag[:-2] if tag.endswith('GP') else tag
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', words)


def event_summary(code, tag):
    return '🏍 {} — {}'.format(SESSION_LABELS[code], gp_name(tag))


def add_alarms(event, description):
    for offset in ALARM_OFFSETS:
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', description)
        alarm.add('trigger', offset)
        event.add_component(alarm)


def transform_events(ics):
    """Filter, relabel and add alarms, leaving everything else untouched."""
    events = []

    for event in Calendar.from_ical(ics).walk('VEVENT'):
        upstream_summary = str(event.get('summary', ''))
        parsed = SUMMARY_PATTERN.match(upstream_summary)
        if parsed is None:
            print('\tSkipping unrecognized summary: {!r}'.format(
                upstream_summary))
            continue

        code = normalize_session_code(parsed.group('code'))
        if code not in KEPT_SESSION_CODES:
            continue

        summary = event_summary(code, parsed.group('gp'))
        event.pop('summary', None)
        event.add('summary', summary)
        add_alarms(event, summary)

        events.append(event)

    return events


def fetch_season(year, required=True):
    """Upstream publishes next season late; a missing optional year is fine."""
    url = SOURCE_URL.format(year=year)
    print('\tFetching {} ...'.format(url))
    response = requests.get(
        url, headers={'User-Agent': APP_NAME}, timeout=20)

    if not required and response.status_code == 404:
        print('\tNot published yet, skipping {}'.format(year))
        return None

    response.raise_for_status()
    return response.text


def build():
    calendar = Calendar()
    calendar.add('prodid', PRODID)
    calendar.add('version', '2.0')
    calendar.add('x-wr-calname', CALENDAR_NAME)
    calendar.add('refresh-interval', REFRESH_INTERVAL,
                 parameters={'VALUE': 'DURATION'})
    calendar.add('x-published-ttl', 'PT12H')

    for position, year in enumerate(season_years()):
        ics = fetch_season(year, required=position == 0)
        if ics is None:
            continue
        for event in transform_events(ics):
            calendar.add_component(event)

    if not calendar.walk('VEVENT'):
        # Better to fail (and keep the previous file in S3) than to overwrite a
        # working calendar with an empty one because upstream changed format.
        raise RuntimeError(
            'No MotoGP events survived; upstream format changed?')

    return calendar
