// IAM role used by codebuild
output "iam_role_codebuild" {
  value = "${aws_iam_role.codebuild.arn}"
}

// IAM role used by codepipeline
output "iam_role_codepipeline" {
  value = "${aws_iam_role.codepipeline.arn}"
}

// Pipeline KMS Key ID
output "kms_key_id" {
  value = "${aws_kms_key.pipeline_key.id}"
}

// Pipeline KMS Key ARN
output "kms_key_arn" {
  value = "${aws_kms_key.pipeline_key.arn}"
}

// Name of the s3 bucket used for storage of PRs and pipeline artifacts
output "s3_bucket_name" {
  value = "${aws_s3_bucket.bucket.id}"
}

// ARN of the s3 bucket used for storage of PRs and pipeline artifacts
output "s3_bucket_arn" {
  value = "${aws_s3_bucket.bucket.arn}"
}

// ARN for pipeline-create lambda function
output "pipeline_create_lambda" {
  value = "${aws_lambda_function.pipeline_create.arn}"
}

// ARN of the pipeline-create IAM role
output "pipeline_create_iam_role_arn" {
  value = "${aws_iam_role.pipeline_create.arn}"
}

// ARN for pipeline-delete lambda function
output "pipeline_delete_lambda" {
  value = "${aws_lambda_function.pipeline_delete.arn}"
}

// ARN of the pipeline-delete IAM role
output "pipeline_delete_iam_role_arn" {
  value = "${aws_iam_role.pipeline_delete.arn}"
}

// ARN for poller-create lambda function
output "poller_create_lambda" {
  value = "${aws_lambda_function.poller_create.arn}"
}

// ARN of the poller-create IAM role
output "poller_create_iam_role_arn" {
  value = "${aws_iam_role.poller_create.arn}"
}

// ARN for poller-delete lambda function
output "poller_delete_lambda" {
  value = "${aws_lambda_function.poller_delete.arn}"
}

// ARN of the poller-delete IAM role
output "poller_delete_iam_role_arn" {
  value = "${aws_iam_role.poller_delete.arn}"
}
