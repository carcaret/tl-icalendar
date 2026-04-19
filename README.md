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

### Devcontainer (recommended)

The project includes a devcontainer with Python, Terraform, and the AWS CLI pre-installed. Open the project in VSCode and when prompted, click **Reopen in Container**.

#### First-time AWS login setup

AWS authentication uses IAM Identity Center (SSO). You need to set it up once in your AWS account before using it:

1. Go to the AWS Console → **IAM Identity Center** → Enable it
2. Create a user (Settings → Users → Add user) and assign it to your account with the desired permission set (e.g. `AdministratorAccess`)
3. Note the **AWS access portal URL** shown in IAM Identity Center dashboard (e.g. `https://something.awsapps.com/start`)

Then, inside the devcontainer, configure the SSO profile once:

```
aws configure sso
```

It will ask for the portal URL, region (`eu-central-1`), and a profile name. Use `default` as the profile name so terraform and boto3 pick it up automatically.

#### Logging in

Every time you open the devcontainer, authenticate with:

```
aws sso login
```

This opens a browser tab — approve the login and you're ready. Credentials live only in the container and expire when it stops.

#### Verify login

```
aws sts get-caller-identity
```

### Running the script

```
python src/tl_icalendar.py
```

### Deploy to AWS

```
make deploy
```