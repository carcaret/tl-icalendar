from unittest.mock import Mock, patch

from icalendar import Calendar, Event

import main


def fake_calendar(uid):
    calendar = Calendar()
    calendar.add('prodid', '-//test//')
    calendar.add('version', '2.0')
    event = Event()
    event.add('uid', uid)
    calendar.add_component(event)
    return calendar


SOURCES = [
    ('starcraft-2', lambda: fake_calendar('sc2')),
    ('motogp', lambda: fake_calendar('motogp')),
]


def test_uploads_one_object_per_source():
    client = Mock()
    with patch.object(main, 'SOURCES', SOURCES), \
            patch.object(main.boto3, 'client', return_value=client):
        main.run()

    keys = [kwargs['Key'] for _, kwargs in client.put_object.call_args_list]
    assert keys == ['starcraft-2.ics', 'motogp.ics']


def test_uploads_with_a_calendar_content_type():
    client = Mock()
    with patch.object(main, 'SOURCES', SOURCES), \
            patch.object(main.boto3, 'client', return_value=client):
        main.run(['motogp'])

    _, kwargs = client.put_object.call_args
    assert kwargs['Bucket'] == 'test-bucket'
    assert kwargs['ContentType'] == 'text/calendar; charset=utf-8'
    assert kwargs['Body'].startswith(b'BEGIN:VCALENDAR')


def test_builds_only_the_selected_source():
    client = Mock()
    with patch.object(main, 'SOURCES', SOURCES), \
            patch.object(main.boto3, 'client', return_value=client):
        main.run(['motogp'])

    keys = [kwargs['Key'] for _, kwargs in client.put_object.call_args_list]
    assert keys == ['motogp.ics']


def test_lambda_handler_builds_the_calendar_from_the_environment(monkeypatch):
    monkeypatch.setenv('CALENDAR', 'motogp')
    with patch.object(main, 'run') as run:
        main.lambda_handler({}, None)

    run.assert_called_once_with(['motogp'])


def test_lambda_handler_builds_everything_without_a_calendar(monkeypatch):
    monkeypatch.delenv('CALENDAR', raising=False)
    with patch.object(main, 'run') as run:
        main.lambda_handler({}, None)

    run.assert_called_once_with(None)


def test_unknown_calendar_is_rejected():
    with patch.object(main, 'SOURCES', SOURCES):
        try:
            main.run(['f1'])
        except SystemExit as error:
            assert 'f1' in str(error)
        else:
            raise AssertionError('expected SystemExit')


def test_dry_run_writes_locally_instead_of_uploading(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = Mock()
    with patch.object(main, 'SOURCES', SOURCES), \
            patch.object(main.boto3, 'client', return_value=client):
        main.run(dry_run=True)

    written = sorted(p.name for p in (tmp_path / 'calendars').iterdir())
    assert written == ['motogp.ics', 'starcraft-2.ics']
    client.put_object.assert_not_called()
