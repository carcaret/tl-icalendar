locals {
  # One Lambda per calendar, each with its own EventBridge schedule, so a
  # scraping failure in one calendar cannot hold back the other. The key is
  # both the source name in `src/main.py` and the object key in S3
  # (`<key>.ics`). Schedules are staggered and expressed in UTC.
  calendars = {
    starcraft-2 = {
      schedule = "cron(0 0 ? * * *)"
      timeout  = 60
    }
    motogp = {
      schedule = "cron(0 3 ? * * *)"
      timeout  = 30
    }
  }
}
