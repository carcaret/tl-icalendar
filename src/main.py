"""Entry point for the ICS calendar generator.

Every source module in `sources/` exposes a `build()` that returns a finished
`Calendar`. The only thing shared across sources is serializing the result and
uploading it to S3, which is what this module does.

Each calendar is deployed as its own Lambda: `CALENDAR` selects which source
that function builds, so a failure in one cannot hold back the other. Without
`CALENDAR` (i.e. locally) every source is built.
"""
import os
import sys

import boto3

from sources import motogp, starcraft2

SOURCES = [
    ('starcraft-2', starcraft2.build),
    ('motogp', motogp.build),
]

CONTENT_TYPE = 'text/calendar; charset=utf-8'
CACHE_CONTROL = 'public, max-age=3600'
LOCAL_OUTPUT_DIR = 'calendars'


def upload(name, calendar):
    bucket = os.environ['BUCKET_NAME']
    key = name + '.ics'
    boto3.client('s3').put_object(
        Bucket=bucket,
        Key=key,
        Body=calendar.to_ical(),
        ContentType=CONTENT_TYPE,
        CacheControl=CACHE_CONTROL,
    )
    return 's3://{}/{}'.format(bucket, key)


def write_local(name, calendar):
    os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)
    path = os.path.join(LOCAL_OUTPUT_DIR, name + '.ics')
    with open(path, 'wb') as f:
        f.write(calendar.to_ical())
    return path


def run(names=None, dry_run=False):
    known = [name for name, _ in SOURCES]
    if names:
        unknown = [name for name in names if name not in known]
        if unknown:
            raise SystemExit('Unknown calendar(s): {}. Available: {}'.format(
                ', '.join(unknown), ', '.join(known)))

    for name, build in SOURCES:
        if names and name not in names:
            continue

        print('Building `{}` ...'.format(name))
        calendar = build()
        print('\t{} events'.format(len(calendar.walk('VEVENT'))))

        if dry_run:
            print('\tWrote {}'.format(write_local(name, calendar)))
        else:
            print('\tUploaded {}'.format(upload(name, calendar)))

    print('GG')


def lambda_handler(event, context):
    calendar = os.environ.get('CALENDAR')
    run([calendar] if calendar else None)
    return True


if __name__ == '__main__':
    args = sys.argv[1:]
    run([a for a in args if not a.startswith('-')] or None,
        dry_run='--dry-run' in args)
