resource "aws_s3_bucket" "calendars" {
  bucket = var.bucket-name
}

# The calendars are subscribed to over plain HTTPS, so the objects must be
# world readable. Buckets are created with public access blocked these days,
# so this has to be turned off explicitly before the policy below can apply.
resource "aws_s3_bucket_public_access_block" "calendars" {
  bucket                  = aws_s3_bucket.calendars.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_ownership_controls" "calendars" {
  bucket = aws_s3_bucket.calendars.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

data "aws_iam_policy_document" "bucket-public-read" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject"
    ]
    resources = [
      "${aws_s3_bucket.calendars.arn}/*"
    ]
    principals {
      type = "*"
      identifiers = [
        "*"
      ]
    }
  }
}

resource "aws_s3_bucket_policy" "calendars" {
  bucket     = aws_s3_bucket.calendars.id
  policy     = data.aws_iam_policy_document.bucket-public-read.json
  depends_on = [aws_s3_bucket_public_access_block.calendars]
}
