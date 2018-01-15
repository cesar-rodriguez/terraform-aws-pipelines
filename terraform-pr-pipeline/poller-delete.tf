/**
  Resources for the poller-delete lambda function
 */

resource "aws_lambda_function" "poller_delete" {
  depends_on       = ["null_resource.poller_delete_dependencies"]
  filename         = ".lambda-zip/poller-delete.zip"
  function_name    = "${var.project_name}-poller-delete"
  role             = "${aws_iam_role.poller_delete.arn}"
  handler          = "poller-delete.lambda_handler"
  source_code_hash = "${base64sha256(file("${path.module}/.lambda-zip/poller-delete.zip"))}"
  runtime          = "python3.6"

  tags {
    Name = "${var.project_name}-poller-delete"
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
resource "aws_lambda_permission" "poller_delete" {
  statement_id  = "schedule"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.poller_delete.function_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.poller_delete_schedule.arn}"
}

// Creates zip file with dependencies every time poller-delete.py is updated
resource "null_resource" "poller_delete_dependencies" {
  triggers {
    lambda_function = "${file("${path.module}/poller-delete/poller-delete.py")}"
  }

  provisioner "local-exec" {
    command = "rm -rf ${path.module}/.lambda-zip/poller-delete-resources"
  }

  provisioner "local-exec" {
    command = "mkdir -p ${path.module}/.lambda-zip/poller-delete-resources"
  }

  provisioner "local-exec" {
    command = "pip install --target=${path.module}/.lambda-zip/poller-delete-resources requests"
  }

  provisioner "local-exec" {
    command = "cp -R ${path.module}/poller-delete/poller-delete.py ${path.module}/.lambda-zip/poller-delete-resources/."
  }

  provisioner "local-exec" {
    command = "cd ${path.module}/.lambda-zip/poller-delete-resources/ && zip -r ../poller-delete.zip ."
  }
}

// Triggers lambda function for polling based on the given time in minutes
resource "aws_cloudwatch_event_rule" "poller_delete_schedule" {
  name                = "${var.project_name}-poller-delete-schedule"
  description         = "Periodically triggers poller-delete lambda"
  schedule_expression = "rate(${var.poller_delete_rate} minutes)"
}

resource "aws_cloudwatch_event_target" "poller_delete_target" {
  rule = "${aws_cloudwatch_event_rule.poller_delete_schedule.name}"
  arn  = "${aws_lambda_function.poller_delete.arn}"
}

// AWS IAM role for poller-delete function
resource "aws_iam_role" "poller_delete" {
  name               = "${var.project_name}-poller-delete-lambda"
  assume_role_policy = "${data.aws_iam_policy_document.lambda_assume_role.json}"
}

data "aws_iam_policy_document" "poller_delete" {
  statement {
    sid = "CreateLogs"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "arn:aws:logs:*:*:log-group:/aws/lambda/${var.project_name}-poller-delete:*",
    ]
  }

  statement {
    sid = "s3"

    actions = [
      "s3:List*",
      "s3:DeleteObject",
      "s3:GetObject*",
    ]

    resources = [
      "${aws_s3_bucket.bucket.arn}*",
    ]
  }
}

resource "aws_iam_policy" "poller_delete" {
  name   = "${aws_iam_role.poller_delete.name}-policy"
  policy = "${data.aws_iam_policy_document.poller_delete.json}"
}

resource "aws_iam_role_policy_attachment" "poller_delete" {
  role       = "${aws_iam_role.poller_delete.name}"
  policy_arn = "${aws_iam_policy.poller_delete.arn}"
}
