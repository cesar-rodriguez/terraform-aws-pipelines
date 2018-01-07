/**
  Resources for the post-comment lambda function
 */

resource "aws_lambda_function" "post_comment" {
  depends_on       = ["null_resource.post_comment_dependencies"]
  filename         = ".lambda-zip/post-comment.zip"
  function_name    = "${var.project_name}-post-comment"
  role             = "${aws_iam_role.post_comment.arn}"
  handler          = "post-comment.lambda_handler"
  source_code_hash = "${base64sha256(file("${path.module}/.lambda-zip/post-comment.zip"))}"
  runtime          = "python3.6"

  tags {
    Name = "${var.project_name}-post-comment"
  }

  environment {
    variables = {
      GITHUB_API_URL = "${var.github_api_url}"

      # GITHUB_PAC       = "${var.github_pac}"
      GITHUB_REPO_NAME = "${var.github_repo_name}"
    }
  }
}

// Creates zip file with dependencies every time post-comment.py is updated
resource "null_resource" "post_comment_dependencies" {
  triggers {
    lambda_function = "${file("${path.module}/post-comment/post-comment.py")}"
  }

  provisioner "local-exec" {
    command = "rm -rf ${path.module}/.lambda-zip/post-comment-resources"
  }

  provisioner "local-exec" {
    command = "mkdir -p ${path.module}/.lambda-zip/post-comment-resources"
  }

  provisioner "local-exec" {
    command = "pip install --target=${path.module}/.lambda-zip/post-comment-resources requests"
  }

  provisioner "local-exec" {
    command = "cp -R ${path.module}/post-comment/post-comment.py ${path.module}/.lambda-zip/post-comment-resources/."
  }

  provisioner "local-exec" {
    command = "cd ${path.module}/.lambda-zip/post-comment-resources/ && zip -r ../post-comment.zip ."
  }
}

// AWS IAM role for post-comment function
resource "aws_iam_role" "post_comment" {
  name               = "${var.project_name}-post-comment-lambda"
  assume_role_policy = "${data.aws_iam_policy_document.assume_role.json}"
}

data "aws_iam_policy_document" "post_comment" {
  statement {
    sid = "CreateLogs"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "arn:aws:logs:*:*:log-group:/aws/lambda/${var.project_name}-post-comment:*",
    ]
  }

  statement {
    sid = "Pipeline"

    actions = [
      "codepipeline:PutJobSuccessResult",
      "codepipeline:PutJobFailureResult",
    ]

    resources = [
      "*",
    ]
  }

  statement {
    sid = "s3"

    actions = [
      "s3:List*",
      "s3:GetObject*",
    ]

    resources = [
      "${aws_s3_bucket.bucket.arn}*",
    ]
  }
}

resource "aws_iam_policy" "post_comment" {
  name   = "${aws_iam_role.post_comment.name}-policy"
  policy = "${data.aws_iam_policy_document.post_comment.json}"
}

resource "aws_iam_role_policy_attachment" "post_comment" {
  role       = "${aws_iam_role.post_comment.name}"
  policy_arn = "${aws_iam_policy.post_comment.arn}"
}
