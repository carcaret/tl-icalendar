# A single package is built from `dist/` and shared by every Lambda; each
# function picks its calendar through the CALENDAR environment variable.
data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/../dist"
  output_path = "${path.module}/../out/lambda-package.zip"
}

data "aws_iam_policy_document" "assume-role" {
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole"
    ]
    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com"
      ]
    }
  }
}

resource "aws_iam_role" "lambda-role" {
  name               = "${var.project-name}_lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume-role.json
}

data "aws_iam_policy_document" "put-object" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject"
    ]
    resources = [
      "${aws_s3_bucket.calendars.arn}/*"
    ]
  }
}

resource "aws_iam_policy" "put-calendar-object-policy" {
  name   = "${var.project-name}_put-calendar-object-policy"
  policy = data.aws_iam_policy_document.put-object.json
}

resource "aws_iam_role_policy_attachment" "put-calendar-object-attachment" {
  role       = aws_iam_role.lambda-role.name
  policy_arn = aws_iam_policy.put-calendar-object-policy.arn
}

data "aws_iam_policy_document" "publish-sns" {
  statement {
    effect = "Allow"
    actions = [
      "sns:Publish"
    ]
    resources = [
      aws_sns_topic.alarms.arn
    ]
  }
}

resource "aws_iam_policy" "publish-sns-policy" {
  name   = "${var.project-name}_publish-sns-policy"
  policy = data.aws_iam_policy_document.publish-sns.json
}

resource "aws_iam_role_policy_attachment" "publish-sns-attachment" {
  role       = aws_iam_role.lambda-role.name
  policy_arn = aws_iam_policy.publish-sns-policy.arn
}

# Without this there are no CloudWatch logs at all, which makes a scraping
# failure invisible.
resource "aws_iam_role_policy_attachment" "lambda-logs-attachment" {
  role       = aws_iam_role.lambda-role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_log_group" "calendar" {
  for_each = local.calendars

  name              = "/aws/lambda/${var.project-name}_${each.key}"
  retention_in_days = 14
}

resource "aws_lambda_function" "calendar" {
  for_each = local.calendars

  function_name    = "${var.project-name}_${each.key}"
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  role             = aws_iam_role.lambda-role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.13"
  # 128 MB left barely 25 MB of headroom when parsing the MotoGP file.
  memory_size = "256"
  timeout     = each.value.timeout

  dead_letter_config {
    target_arn = aws_sns_topic.alarms.arn
  }

  environment {
    variables = {
      BUCKET_NAME = var.bucket-name
      CALENDAR    = each.key
    }
  }

  depends_on = [aws_cloudwatch_log_group.calendar]
}
