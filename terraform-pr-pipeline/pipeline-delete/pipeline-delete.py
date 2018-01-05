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

# Global vars
bucket = os.environ['BUCKET_NAME']
project_name = os.environ['PROJECT_NAME']


def lambda_handler(event, context):
    """
    Deletes pipeline resources associated to deleted s3 object
    """
    pr_number = event['Records'][0]['s3']['object']['key'].split('/')[0]

    logger.debug('Deleting pipeline')
    codepipeline.delete_pipeline(name='{}-terraform-pr-pipeline-{}'.format(
        project_name, pr_number))

    logger.debug('Deleting terraform fmt codebuild project')
    codepipeline.delete_project(name='{}-terraform-pr-fmt-{}'.format(
        project_name, pr_number))

    logger.debug('Deleting terrascan codebuild project')
    codepipeline.delete_project(name='{}-terraform-pr-terrascan-{}'.format(
        project_name, pr_number))

    logger.debug('Deleting terraform plan codebuild project')
    codepipeline.delete_project(name='{}-terraform-pr-plan-{}'.format(
        project_name, pr_number))
