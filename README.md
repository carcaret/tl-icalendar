# ICS Calendars

Generator of subscribable iCalendar (`.ics`) files. Each calendar is built by a
source module in `src/sources/`, serialized and uploaded to a public S3 bucket,
where calendar apps can subscribe to it by URL.

Currently available calendars:

| Calendar | URL | Updated |
| --- | --- | --- |
| StarCraft 2 (S-Tier tournaments) | https://carcaret-calendars.s3.eu-central-1.amazonaws.com/starcraft-2.ics | daily, 00:00 UTC |
| MotoGP (races) | https://carcaret-calendars.s3.eu-central-1.amazonaws.com/motogp.ics | daily, 03:00 UTC |

## The calendars

### StarCraft 2

Converts [TeamLiquid's XML calendar](http://www.teamliquid.net/calendar/xml/calendar.xml)
into iCalendar format, keeping only the events that belong to a tournament in
Liquipedia's S-Tier category (and dropping replay casts). Event times are in
`Asia/Seoul`, the timezone TeamLiquid publishes in.

### MotoGP

Takes [nixxo's MotoGP ICS](https://nixxo.github.io/calendars/) for the current
season and makes it usable as a subscription:

- **Filters the sessions** down to the Sunday race. Qualifying and the
  Saturday sprint are dropped; adding them back is one line
  (`KEPT_SESSION_CODES` at the top of `src/sources/motogp.py`).
- **Injects two alarms** per event, 60 and 10 minutes before the start, both
  `ACTION:DISPLAY` (audio and email alarms are unevenly supported on iOS).
  Upstream ships no alarms at all.
- **Rewrites the summaries**, from upstream codes like
  `[MotoGP] RAC #SanMarinoGP` to `San Marino — MotoGP`: where it is first, then
  the series. iOS shows the event summary in the notification, not the alarm
  description, so this is what you actually read when your phone buzzes.
- **Normalizes upstream's numbered race codes** (the Catalunya race ships as
  `RAC2` instead of `RAC`).
- **Keeps the upstream UID** of every event, so when upstream moves a session
  time your calendar app updates the event instead of duplicating it.

The season year is derived from the clock, so there is nothing to edit in
December: from November on, next season's file is pulled as well (if upstream
has published it already) and merged with the current one.

## Subscribing on iOS (recommended)

Subscribe **natively**, not through Google Calendar, or the embedded alarms are
lost:

1. **Settings → Apps → Calendar → Calendar Accounts → Add Account → Other →
   Add Subscribed Calendar**
2. Paste the calendar URL and tap **Next**
3. Leave **Remove Alarms** **OFF** — this is the important one. With it on, iOS
   strips the alarms that are the whole point of the MotoGP calendar.
4. **Save**

> Adding the calendar through Google Calendar instead will work, but Google
> discards the `VALARM` components, so you get the events without any warning.
> If you go that route you have to add notifications per calendar by hand.

## Subscribing with Google Calendar

- Go to https://calendar.google.com/calendar/r/settings/addbyurl
- Paste the URL of the calendar
- Click `Add Calendar`, the calendar URL should appear in the sidebar
- Click the calendar in the sidebar to give it a nice name and add event
  notifications (the embedded alarms do not survive, see above)

## How it is deployed

- One **Lambda per calendar** (`ics-calendars_starcraft-2`,
  `ics-calendars_motogp`), all sharing the same deployment package. The
  `CALENDAR` environment variable tells each function which source to build.
- One **EventBridge schedule per Lambda**, so a scraping failure in one
  calendar never stops the other from being regenerated.
- Failures go to the `ics-calendars-alarms` SNS topic (Lambda dead letter
  config), and logs to CloudWatch with 14 days of retention.
- All of it lives in `tf/` as a single Terraform state.

```
src/
  main.py               entry point: loops over the sources, uploads to S3
  sources/
    starcraft2.py       builds events from TeamLiquid's XML
    motogp.py           transforms the upstream MotoGP ICS
tf/                     s3, lambda, schedule, sns
tests/
```

## Development

### Devcontainer (recommended)

The project includes a devcontainer with Python, Terraform, and the AWS CLI
pre-installed. Open the project in VSCode and when prompted, click **Reopen in
Container**.

#### First-time AWS login setup

AWS authentication uses IAM Identity Center (SSO). You need to set it up once in
your AWS account before using it:

1. Go to the AWS Console → **IAM Identity Center** → Enable it
2. Create a user (Settings → Users → Add user) and assign it to your account
   with the desired permission set (e.g. `AdministratorAccess`)
3. Note the **AWS access portal URL** shown in IAM Identity Center dashboard
   (e.g. `https://something.awsapps.com/start`)

Then, inside the devcontainer, configure the SSO profile once:

```
aws configure sso
```

It will ask for the portal URL, region (`eu-central-1`), and a profile name. Use
`default` as the profile name so terraform and boto3 pick it up automatically.

#### Logging in

Every time you open the devcontainer, authenticate with:

```
aws sso login
```

This opens a browser tab — approve the login and you're ready. Credentials live
only in the container and expire when it stops.

#### Verify login

```
aws sts get-caller-identity
```

### Running the generator

Write the calendars to `calendars/` without touching S3:

```
python src/main.py --dry-run
```

Build a single calendar (names are the keys of `SOURCES` in `src/main.py`):

```
python src/main.py --dry-run motogp
```

Without `--dry-run` it uploads to the bucket in `BUCKET_NAME`.

### Tests

```
make test               # unit tests
make test-integration   # hits TeamLiquid, Liquipedia and the MotoGP source
```

### Deploy to AWS

```
make deploy
```

Bundles the runtime dependencies plus `src/` into `dist/`, then runs
`terraform apply` in `tf/`.

### Adding a calendar

1. Add a module to `src/sources/` exposing a `build()` that returns an
   `icalendar.Calendar`.
2. Add it to `SOURCES` in `src/main.py`. The name becomes the object key
   (`<name>.ics`).
3. Add an entry to `locals.calendars` in `tf/locals.tf` with its schedule and
   timeout — the Lambda, the EventBridge rule and the permissions are created
   from it.
