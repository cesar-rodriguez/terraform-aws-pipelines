// Allows IAM roles to be assumed by lambda
data "aws_iam_policy_document" "codepipeline_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type = "Service"

      identifiers = [
        "codepipeline.amazonaws.com",
      ]
    }
  }
}

// AWS IAM role for codepipeline
resource "aws_iam_role" "codepipeline" {
  name               = "${var.project_name}-codepipeline"
  assume_role_policy = "${data.aws_iam_policy_document.codepipeline_assume_role.json}"
}

data "aws_iam_policy_document" "codepipeline_service" {
  statement {
    sid = "BuildPolicy"

    actions = [
      "codebuild:StartBuild",
      "codebuild:StopBuild",
      "codebuild:BatchGetBuilds",
    ]

    resources = [
      "arn:aws:codebuild:${var.aws_region}:${data.aws_caller_identity.current.account_id}:project/${var.project_name}-terraform-pr*",
    ]
  }

  statement {
    sid = "S3Policy"

    actions = [
      "s3:Get*",
      "s3:Put*",
    ]

    resources = [
      "${aws_s3_bucket.bucket.arn}*",
    ]
  }
}

resource "aws_iam_policy" "codepipeline_service" {
  name   = "${aws_iam_role.codepipeline.name}-policy"
  policy = "${data.aws_iam_policy_document.codepipeline_service.json}"
}

resource "aws_iam_role_policy_attachment" "codepipeline_service" {
  role       = "${aws_iam_role.codepipeline.name}"
  policy_arn = "${aws_iam_policy.codepipeline_service.arn}"
}
