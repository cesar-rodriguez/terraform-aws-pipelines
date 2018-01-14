import os
import logging
import requests
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
s3 = boto3.client('s3')

# Global vars
# pac = os.environ['GITHUB_PAC']
github_api_url = os.environ['GITHUB_API_URL']
repo = os.environ['GITHUB_REPO_NAME']
bucket = os.environ['BUCKET_NAME']


def is_pr_open(pr_number):
    """
    Returns True if the pull request's status is open
    """
    pr_url = '{}/repos/{}/pulls/{}'.format(
        github_api_url,
        repo,
        pr_number)
    logger.debug('Checking if PR is open in this URL: {}'.format(pr_url))
    if requests.get(pr_url).json()['state'] == 'open':
        logger.debug('PR open True')
        return True
    logger.debug('PR open False')
    return False


def lambda_handler(event, context):
    """
    Deletes objects in S3 for PRs that are no longer open
    """
    logger.debug('Removing resources for PRs no longer open')
    s3_resources = s3.list_objects_v2(Bucket=bucket)['Contents']
    objects_to_delete = []
    for resource in s3_resources:
        if 'terraform' in resource['Key']:
            continue
        if not is_pr_open(resource['Key'].split('/')[0]):
            objects_to_delete.append({
                'Key': resource['Key']
            })

    if objects_to_delete == []:
        logger.info('All PRs still open')
    else:
        s3.delete_objects(
            Bucket=bucket,
            Delete={
                'Objects': objects_to_delete,
                'Quiet': False
            }
        )
        logger.info('The following objects have been deleted: {}'.format(
            objects_to_delete))
