/**
  Resources for the poller-create lambda function
 */

resource "aws_lambda_function" "poller_create" {
  depends_on       = ["null_resource.poller_create_dependencies"]
  filename         = ".lambda-zip/poller-create.zip"
  function_name    = "${var.project_name}-poller-create"
  role             = "${aws_iam_role.poller_create.arn}"
  handler          = "poller-create.lambda_handler"
  source_code_hash = "${base64sha256(file("${path.module}/.lambda-zip/poller-create.zip"))}"
  runtime          = "python3.6"

  tags {
    Name = "${var.project_name}-poller-create"
  }

  environment {
    variables = {
      GITHUB_API_URL = "${var.github_api_url}"

      # GITHUB_PAC       = "${var.github_pac}"
      GITHUB_REPO_NAME = "${var.github_repo_name}"
      BUCKET_NAME      = "${aws_s3_bucket.bucket.id}"
    }
  }
}

// Allows cloudwatch to trigger the function
resource "aws_lambda_permission" "poller_create" {
  statement_id  = "schedule"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.poller_create.function_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.poller_create_schedule.arn}"
}

// Creates zip file with dependencies every time poller-create.py is updated
resource "null_resource" "poller_create_dependencies" {
  triggers {
    lambda_function = "${file("${path.module}/poller-create/poller-create.py")}"
  }

  provisioner "local-exec" {
    command = "rm -rf ${path.module}/.lambda-zip/poller-create-resources"
  }

  provisioner "local-exec" {
    command = "mkdir -p ${path.module}/.lambda-zip/poller-create-resources"
  }

  provisioner "local-exec" {
    command = "pip install --target=${path.module}/.lambda-zip/poller-create-resources requests"
  }

  provisioner "local-exec" {
    command = "cp -R ${path.module}/poller-create/poller-create.py ${path.module}/.lambda-zip/poller-create-resources/."
  }

  provisioner "local-exec" {
    command = "cd ${path.module}/.lambda-zip/poller-create-resources/ && zip -r ../poller-create.zip ."
  }
}

// Triggers lambda function for polling based on the given time in minutes
resource "aws_cloudwatch_event_rule" "poller_create_schedule" {
  name                = "${var.project_name}-poller-create-schedule"
  description         = "Periodically triggers poller-create lambda"
  schedule_expression = "rate(90 minutes)"
}

resource "aws_cloudwatch_event_target" "poller_create_target" {
  rule = "${aws_cloudwatch_event_rule.poller_create_schedule.name}"
  arn  = "${aws_lambda_function.poller_create.arn}"
}

// AWS IAM role for poller-create function
resource "aws_iam_role" "poller_create" {
  name               = "${var.project_name}-poller-create-lambda"
  assume_role_policy = "${data.aws_iam_policy_document.assume_role.json}"
}

data "aws_iam_policy_document" "poller_create" {
  statement {
    sid = "CreateLogs"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "arn:aws:logs:*:*:log-group:/aws/lambda/${var.project_name}-poller-create:*",
    ]
  }

  statement {
    sid = "s3"

    actions = [
      "s3:List*",
      "s3:GetObjectTagging",
      "s3:PutObject",
      "s3:PutObjectTagging",
    ]

    resources = [
      "${aws_s3_bucket.bucket.arn}*",
    ]
  }
}

resource "aws_iam_policy" "poller_create" {
  name   = "${aws_iam_role.poller_create.name}-policy"
  policy = "${data.aws_iam_policy_document.poller_create.json}"
}

resource "aws_iam_role_policy_attachment" "poller_create" {
  role       = "${aws_iam_role.poller_create.name}"
  policy_arn = "${aws_iam_policy.poller_create.arn}"
}
