import os
import logging
import boto3

# Configuring logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers[0].setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
))
logging.getLogger('boto3').setLevel(logging.ERROR)
logging.getLogger('botocore').setLevel(logging.ERROR)

# Boto clients
codepipeline = boto3.client('codepipeline')
codebuild = boto3.client('codebuild')
s3 = boto3.client('s3')

# Global vars
bucket = os.environ['BUCKET_NAME']
project_name = os.environ['PROJECT_NAME']


def object_exists(key):
    """
    Determines if objet exists in S3 bucket
    """
    try:
        s3.get_object(Bucket=bucket, Key=key)
    except s3.exceptions.NoSuchKey:
        return False
    return True


def delete_pipeline(pipeline_name):
    """
    Deletes the specified AWS CodePipeline pipeline
    """
    logger.info('Deleting pipeline: {}'.format(pipeline_name))
    codepipeline.delete_pipeline(name=pipeline_name)


def delete_codebuild_project(project_name):
    """
    Deletes the specified AWS CodeBuild project
    """
    logger.info('Deleting codebuild project: {}'.format(
        project_name))
    codebuild.delete_project(name=project_name)


def lambda_handler(event, context):
    """
    Deletes pipeline resources associated to S3 object that no longer exists
    """
    repo_object = event['Records'][0]['s3']['object']['key']

    if 'repo.zip' in repo_object and not object_exists(repo_object):
        logger.info('Object no longer exists at: {}'.format(repo_object))
        pr_number = repo_object.split('/')[0]

        delete_pipeline('{}-terraform-pr-pipeline-{}'.format(
            project_name, pr_number))

        delete_codebuild_project('{}-terraform-pr-fmt-{}'.format(
            project_name, pr_number))

        delete_codebuild_project('{}-terraform-pr-terrascan-{}'.format(
            project_name, pr_number))

        delete_codebuild_project('{}-terraform-pr-plan-{}'.format(
            project_name, pr_number))
