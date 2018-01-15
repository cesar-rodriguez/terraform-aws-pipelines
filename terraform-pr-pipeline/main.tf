/**
  # AWS terraform pull request pipeline
  Provisions CI/CD pipeline for terraform pull request reviews. A new pipeline (AWS CodePipeline) is created for each new pull request in the given GitHub repository. The solution uses AWS lambda to sync contents of PRs with S3 and to create the pipeline. CodeBuild is used to check for terraform fmt, runs terrascan for static code analysis, and comments results into the PR.

  The pipeline will only perform tests on directories that contain modified files only. Testing that terraform plan/apply exesutes without errors will be done on /tests directories assuming that such directory exists on each template directory. Here's an example directory tree:
```
  .
|-- main.tf
|-- tests
|   `-- main.tf
|-- tf_templates
|   |-- main.tf
|   `-- tests
|       `-- main.tf
|-- tf_another_dir
|   |-- main.tf
|   `-- tests
|       `-- main.tf
`-- tf_yet_another_dir
    |-- main.tf
    `-- tests
        `-- main.tf
```

  Prior to running the terraform templates for the first time. Execute setup.sh to prepopulate required zip files.

  ## poller-create lambda
  Funtion that is triggered by default every 5 minutes to poll the repository for open pull requets. A zip file of latest commit for each pull request is saved into an S3 bucket.

  ## poller-delete lambda
  Function that is triggered by default every 60 minutes to remove zip files from S3 corresponding to pull requests no longer open.

  ## pipeline-create lambda
  Triggered each time there's a zip file uploaded to S3. This function creates an AWS CodePipeline pipeline if one doesn't exists yet for that pull request.

  ## pipeline-delete lambda
  Triggered each time there's a zip file deleted from S3. This function deletes the pipeline for closed PRs.
 */

provider aws {
  profile = "${var.aws_profile}"
  region  = "${var.aws_region}"
}

// Used to get AWS IAM account number
data "aws_caller_identity" "current" {}

// Stores PR zip files and terraform statefiles
resource "aws_s3_bucket" "bucket" {
  bucket = "${var.project_name}-terraform-pr-pipeline"
  acl    = "private"

  versioning {
    enabled = true
  }

  lifecycle_rule = {
    id      = "deletein30days"
    prefix  = "/"
    enabled = true

    expiration {
      days = "30"
    }
  }

  force_destroy = "True"
}

// Allows IAM roles to be assumed by lambda
data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type = "Service"

      identifiers = [
        "lambda.amazonaws.com",
      ]
    }
  }
}

// S3 trigger event config
resource "aws_s3_bucket_notification" "pipeline_create_delete" {
  bucket = "${aws_s3_bucket.bucket.id}"

  lambda_function {
    lambda_function_arn = "${aws_lambda_function.pipeline_create.arn}"
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = "repo.zip"
  }

  lambda_function {
    lambda_function_arn = "${aws_lambda_function.pipeline_delete.arn}"
    events              = ["s3:ObjectRemoved:*"]
    filter_suffix       = "repo.zip"
  }
}
