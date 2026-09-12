output "calendar-urls" {
  value = {
    for name, _ in local.calendars :
    name => "https://${var.bucket-name}.s3.${var.region}.amazonaws.com/${name}.ics"
  }
}
