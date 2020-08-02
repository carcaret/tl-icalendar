data aws_iam_policy_document bucket-public-read {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject"
    ]
    resources = [
      "arn:aws:s3:::${var.bucket-name}/*"
    ]
    principals {
      identifiers = [
        "*"]
      type = "AWS"
    }
  }
}

resource aws_s3_bucket sc2-calendar {
  bucket = var.bucket-name
  acl = "private"
  policy = data.aws_iam_policy_document.bucket-public-read.json
}

data aws_iam_policy_document assume-role {
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole"]
    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com"]
    }
  }
}

data archive_file lambda_package {
  type = "zip"
  source_dir = "${path.module}/../dist"
  output_path = "${path.module}/../out/lambda-package.zip"
}

resource aws_iam_role lambda-role {
  name = "${var.project-name}_lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume-role.json
}

resource aws_lambda_function create-calendar {
  filename = data.archive_file.lambda_package.output_path
  function_name = "${var.project-name}_creator"
  role = aws_iam_role.lambda-role.arn
  handler = "tl_icalendar.event_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime = "python3.6"
  memory_size = "128"
  timeout = 30
  dead_letter_config {
    target_arn = aws_sns_topic.alarms.arn
  }
  environment {
    variables = {
      BUCKET_NAME = var.bucket-name
    }
  }
}

data aws_iam_policy_document put-object {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject"
    ]
    resources = [
      "arn:aws:s3:::${var.bucket-name}/*"
    ]
  }
}

resource aws_iam_policy put-calendar-object-policy {
  name = "${var.project-name}_put-calendar-object-policy"
  policy = data.aws_iam_policy_document.put-object.json
}

resource aws_iam_role_policy_attachment put-calendar-object-attachment {
  role = aws_iam_role.lambda-role.name
  policy_arn = aws_iam_policy.put-calendar-object-policy.arn
}

data aws_iam_policy_document publish-sns {
  statement {
    effect = "Allow"
    actions = [
      "sns:Publish"
    ]
    resources = [
      "arn:aws:sns:${var.region}:${var.account}:${aws_sns_topic.alarms.arn}"
    ]
  }
}

resource aws_iam_policy publish-sns-policy {
  name = "${var.project-name}_publish-sns-policy"
  policy = data.aws_iam_policy_document.publish-sns.json
}

resource aws_iam_role_policy_attachment publish-sns-attachment {
  role = aws_iam_role.lambda-role.name
  policy_arn = aws_iam_policy.publish-sns-policy.arn
}

resource aws_cloudwatch_event_rule calendar-trigger {
  name        = "${aws_lambda_function.create-calendar.function_name}-trigger"
  schedule_expression = "cron(0 0 ? * * *)"
}

resource aws_cloudwatch_event_target calendar-trigger-target {
  target_id = "${aws_lambda_function.create-calendar.function_name}-trigger"
  arn = aws_lambda_function.create-calendar.arn
  rule = aws_cloudwatch_event_rule.calendar-trigger.name
}

resource aws_lambda_permission calendar-trigger-permission {
  statement_id = "AllowExecutionFromCloudWatch"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create-calendar.function_name
  principal = "events.amazonaws.com"
  source_arn = aws_cloudwatch_event_rule.calendar-trigger.arn
}

resource aws_sns_topic alarms {
  name = "${var.project-name}-alarms"
}