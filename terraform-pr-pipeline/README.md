# AWS terraform pull request pipeline
Provisions CI/CD pipeline for terraform pull request reviews. A new pipeline (AWS CodePipeline) is created for each new pull request in the given GitHub repository. The solution uses AWS lambda to sync contents of PRs with S3 and to create the pipeline. CodeBuild is used to check for terraform fmt, runs terrascan for static code analysis, and comments results into the PR.

## poller-create lambda
Funtion that is triggered by default every 5 minutes to poll the repository for open pull requets. A zip file of latest commit for each pull request is saved into an S3 bucket.

## poller-delete lambda
Function that is triggered by default every 60 minutes to remove zip files from S3 corresponding to pull requests no longer open.

## pipeline-create lambda
Triggered each time there's a zip file uploaded to S3. This function creates an AWS CodePipeline pipeline if one doesn't exists yet for that pull request.

## pipeline-delete lambda
Triggered each time there's a zip file deleted from S3. This function deletes the pipeline for closed PRs.


## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|:----:|:-----:|:-----:|
| aws_profile | AWS credentials profile to use | string | - | yes |
| aws_region | AWS region where resources are provisioned | string | - | yes |
| github_api_url | API URL for GitHub | string | `https://api.github.com` | no |
| github_repo_name | Name of the repository to track pull requests in org/repo format (e.g. cesar-rodriguez/test-repo) | string | - | yes |
| poller_create_rate | Rate in minutes for polling the GitHub repository for open pull requests | string | `5` | no |
| poller_delete_rate | Rate in minutes for polling the GitHub repository to check if PRs are still open | string | `60` | no |
| project_name | All resources will be prepended with this name | string | - | yes |

## Outputs

| Name | Description |
|------|-------------|
| poller_create_lambda | ARN for poller-create lambda function |
| poller_delete_lambda | ARN for poller-delete lambda function |
| s3_bucket_name | Name of the s3 bucket used for storage of PRs |

