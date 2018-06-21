# TeamLiquid iCalendar

Python script which converts TeamLiquid's XML calendar into iCalendar format to be used with Google Calendar and other calendar applications. Uploads calendar files for every event type to Amazon S3 bucket.

## How it works

The script generates iCalendar files for every event type in TeamLiquid's calendar and uploads them into Amazon S3 bucket.

Currently available calendars (updated every 60 minutes):

- https://s3.amazonaws.com/tl-icalendar/starcraft-2.ics
- https://s3.amazonaws.com/tl-icalendar/brood-war.ics
- https://s3.amazonaws.com/tl-icalendar/cs-go.ics
- https://s3.amazonaws.com/tl-icalendar/overwatch.ics
- https://s3.amazonaws.com/tl-icalendar/heroes-of-the-storm.ics
- https://s3.amazonaws.com/tl-icalendar/other.ics

If new event type appears in TeamLiquid calendar, the script will automatically create a new calendar for it.

## Using the calendars with Google Calendar

Below steps describe how to use the calendars with Google Calendar.

- Go to https://calendar.google.com/calendar/r/settings/addbyurl
- Paste the URL of the calendar, e.g. `https://s3.amazonaws.com/tl-icalendar/starcraft-2.ics`
- Click `Add Calendar`, the calendar URL should appear in the sidebar
- Click the calendar in the sidebar to give it a nice name, e.g. `StarCraft 2`, add event notifications etc...
- You will never miss an important event again!

![Google Calendar Demo](https://s3.amazonaws.com/tl-icalendar/demo.png)

## Development

Create virtualenv with Python 3 for your project. Example using virtualenvwrapper:

```
mkvirtualenv -p python3 tl-icalendar
workon tl-icalendar
```

Clone the project and install project requirements into your virtualenv.

```
git clone https://github.com/mckdev/tl-icalendar/
cd tl-icalendar
pip install -r requirements.txt
```

### Configure Amazon S3 upload (optional)

If you want the S3 upload to work, create AWS configuration file in your user directory.

- Linux: `~/.aws/credentials`
- Windows: `C:\Users\username\.aws\credentials`

The content of the `credentials` file should look like this:

```
[default]
aws_access_key_id =  YOUR_AWS_ACCESS_KEY_ID
aws_secret_access_key = YOUR_AWS_SECRET_ACCESS_KEY
```

You will also need to create a bucket with public read access and modify `BUCKET_NAME` variable inside `tl-icalendar.py` to match your S3 bucket name.

### Working without S3

The calendars are always stored locally in `calendars/` directory, so if you don't want to use S3 upload, simply comment out the `upload_calendars()` line inside `run()` function.

### Running the script

Run the script with:

```
python tl_icalendar.py
```

### Deploy to Heroku & S3

This script is ready for Heroku + Amazon S3 deployment.

1. Create S3 bucket with public read access and a user with full S3 access permissions. 
2. Change the `BUCKET_NAME` variable in the script to match your S3 bucket name.
2. Create new Heroku app and set your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` config vars.
3. Push the script to heroku master (it will run once after that so check your S3 bucket for the calendar files).
4. Set up the Heroku scheduler to run `python tl_calendar.py` at your desired interval.
