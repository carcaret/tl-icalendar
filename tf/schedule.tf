resource "aws_cloudwatch_event_rule" "calendar-trigger" {
  for_each = local.calendars

  name                = "${aws_lambda_function.calendar[each.key].function_name}-trigger"
  schedule_expression = each.value.schedule
}

resource "aws_cloudwatch_event_target" "calendar-trigger-target" {
  for_each = local.calendars

  target_id = "${aws_lambda_function.calendar[each.key].function_name}-trigger"
  arn       = aws_lambda_function.calendar[each.key].arn
  rule      = aws_cloudwatch_event_rule.calendar-trigger[each.key].name
}

resource "aws_lambda_permission" "calendar-trigger-permission" {
  for_each = local.calendars

  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.calendar[each.key].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.calendar-trigger[each.key].arn
}
