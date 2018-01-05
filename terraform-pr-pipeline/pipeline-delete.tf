/**
  Resources for the pipeline-delete lambda function
 */

resource "aws_lambda_function" "pipeline_delete" {
  depends_on       = ["null_resource.pipeline_delete_dependencies"]
  filename         = ".lambda-zip/pipeline-delete.zip"
  function_name    = "${var.project_name}-pipeline-delete"
  role             = "${aws_iam_role.pipeline_delete.arn}"
  handler          = "pipeline-delete.lambda_handler"
  source_code_hash = "${base64sha256(file("${path.module}/.lambda-zip/pipeline-delete.zip"))}"
  runtime          = "python3.6"

  tags {
    Name = "${var.project_name}-pipeline-delete"
  }

  environment {
    variables = {
      BUCKET_NAME  = "${aws_s3_bucket.bucket.id}"
      PROJECT_NAME = "${var.project_name}"
    }
  }
}

// Allows s3 to trigger the function
resource "aws_lambda_permission" "pipeline_delete" {
  statement_id  = "schedule"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.pipeline_delete.function_name}"
  principal     = "s3.amazonaws.com"
  source_arn    = "${aws_s3_bucket.bucket.arn}"
}

// Creates zip file with dependencies every time pipeline-delete.py is updated
resource "null_resource" "pipeline_delete_dependencies" {
  triggers {
    lambda_function = "${file("${path.module}/pipeline-delete/pipeline-delete.py")}"
  }

  provisioner "local-exec" {
    command = "rm -rf ${path.module}/.lambda-zip/pipeline-delete-resources"
  }

  provisioner "local-exec" {
    command = "mkdir -p ${path.module}/.lambda-zip/pipeline-delete-resources"
  }

  provisioner "local-exec" {
    command = "pip install --target=${path.module}/.lambda-zip/pipeline-delete-resources requests"
  }

  provisioner "local-exec" {
    command = "cp -R ${path.module}/pipeline-delete/pipeline-delete.py ${path.module}/.lambda-zip/pipeline-delete-resources/."
  }

  provisioner "local-exec" {
    command = "cd ${path.module}/.lambda-zip/pipeline-delete-resources/ && zip -r ../pipeline-delete.zip ."
  }
}

// AWS IAM role for pipeline-delete function
resource "aws_iam_role" "pipeline_delete" {
  name               = "${var.project_name}-pipeline-delete-lambda"
  assume_role_policy = "${data.aws_iam_policy_document.assume_role.json}"
}

data "aws_iam_policy_document" "pipeline_delete" {
  statement {
    sid = "CreateLogs"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-pipeline-delete:*",
    ]
  }

  statement {
    sid = "CodeBuildAccess"

    actions = [
      "codebuild:DeleteProject",
    ]

    resources = [
      "arn:aws:codebuild:${var.aws_region}:${data.aws_caller_identity.current.account_id}:project/${var.project_name}*",
    ]
  }

  statement {
    sid = "CodePipelineAccess"

    actions = [
      "codepipeline:DeletePipeline",
    ]

    resources = [
      "arn:aws:codepipeline:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.project_name}*",
    ]
  }
}

resource "aws_iam_policy" "pipeline_delete" {
  name   = "${aws_iam_role.pipeline_delete.name}-policy"
  policy = "${data.aws_iam_policy_document.pipeline_delete.json}"
}

resource "aws_iam_role_policy_attachment" "pipeline_delete" {
  role       = "${aws_iam_role.pipeline_delete.name}"
  policy_arn = "${aws_iam_policy.pipeline_delete.arn}"
}
