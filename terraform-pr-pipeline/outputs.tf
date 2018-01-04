/**
  Common resources
 */

// Name of the s3 bucket used for storage of PRs
output "s3_bucket_name" {
  value = "${aws_s3_bucket.bucket.id}"
}

/**
  poller-create resources
 */

// ARN for poller-create lambda function
output "poller_create_lambda" {
  value = "${aws_lambda_function.poller_create.arn}"
}

// ARN for poller-delete lambda function
output "poller_delete_lambda" {
  value = "${aws_lambda_function.poller_delete.arn}"
}

// ARN for pipeline-create lambda function
output "pipeline_create_lambda" {
  value = "${aws_lambda_function.pipeline_create.arn}"
}
