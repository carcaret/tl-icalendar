# TeamLiquid iCalendar

Python script which converts TeamLiquid's XML calendar into iCalendar format to be used with Google Calendar and other calendar applications. Uploads calendar files for every event type to Amazon S3 bucket.

## How it works

The script generates iCalendar files for Premier Starcraft 2 Tournaments in TeamLiquid's calendar and uploads them into Amazon S3 bucket.

Currently available calendars (updated every day at midnight):

- https://carcaret-sc2-calendar.s3.eu-central-1.amazonaws.com/starcraft-2.ics

## Using the calendars with Google Calendar

Below steps describe how to use the calendars with Google Calendar.

- Go to https://calendar.google.com/calendar/r/settings/addbyurl
- Paste the URL of the calendar, e.g. `https://s3.amazonaws.com/tl-icalendar/starcraft-2.ics`
- Click `Add Calendar`, the calendar URL should appear in the sidebar
- Click the calendar in the sidebar to give it a nice name, e.g. `StarCraft 2`, add event notifications etc...
- You will never miss an important event again!

![Google Calendar Demo](https://s3.amazonaws.com/tl-icalendar/demo.png)

## Development

Clone the project and install project requirements into your virtualenv.

```
git clone https://github.com/carcaret/tl-icalendar.git
cd tl-icalendar
pipenv install
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

The calendars are always stored locally in `/tmp` directory, so if you don't want to use S3 upload, simply comment out the `upload_calendars()` line inside `run()` function.

### Running the script

Run the script with:

```
python tl_icalendar.py
```

### Deploy to AWS

Run the Makefile:

```
make deploy
```