# Dead letter target: a Lambda that fails every retry publishes here.
resource "aws_sns_topic" "alarms" {
  name = "${var.project-name}-alarms"
}
