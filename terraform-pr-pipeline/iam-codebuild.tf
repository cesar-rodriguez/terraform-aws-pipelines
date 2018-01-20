// Allows IAM roles to be assumed by lambda
data "aws_iam_policy_document" "codebuild_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type = "Service"

      identifiers = [
        "codebuild.amazonaws.com",
      ]
    }
  }
}

// AWS IAM role for codebuild
resource "aws_iam_role" "codebuild" {
  name               = "${var.project_name}-codebuild"
  assume_role_policy = "${data.aws_iam_policy_document.codebuild_assume_role.json}"
}

data "aws_iam_policy_document" "codebuild_service" {
  statement {
    sid = "CloudWatchLogsPolicy"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/codebuild/${var.project_name}-terraform-pr*",
    ]
  }

  statement {
    sid = "S3Policy"

    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:PutObject",
    ]

    resources = [
      "${aws_s3_bucket.bucket.arn}*",
    ]
  }

  statement {
    sid = "SSMAccess"

    actions = [
      "ssm:GetParameters",
    ]

    resources = [
      "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${var.project_name}-terraform-pr*",
    ]
  }
}

resource "aws_iam_policy" "codebuild_service" {
  name   = "${aws_iam_role.codebuild.name}-policy"
  policy = "${data.aws_iam_policy_document.codebuild_service.json}"
}

resource "aws_iam_role_policy_attachment" "codebuild_service" {
  role       = "${aws_iam_role.codebuild.name}"
  policy_arn = "${aws_iam_policy.codebuild_service.arn}"
}
