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


def get_open_pull_requests():
    """
    Returns JSON of open PRs on given repo
    """
    pulls_url = '{}/repos/{}/pulls'.format(
        github_api_url,
        repo)
    logger.info('Loading open pull requests from: {}'.format(pulls_url))
    r = requests.get(pulls_url)

    if r.status_code != 200:
        logger.error('GH pull URL status code error: {}'.format(
            r.status_code))
        raise Exception('GH pull URL status code != 200')

    return r.json()


def object_exists(key):
    """
    Determines if objet exists in S3 bucket
    """
    try:
        s3.get_object(Bucket=bucket, Key=key)
    except s3.exceptions.NoSuchKey:
        return False
    return True


def is_pr_synced(pr_number, sha):
    """
    Checks if there's a corresponding S3 object for the given pr_number and sha
    Assumes that zip files are at pr_number/repo.zip and that they are
    tagged with "Key":"latest_commit","Value":sha
    """
    response = s3.list_objects_v2(Bucket=bucket)
    repo_zip = '{}/repo.zip'.format(pr_number)
    try:
        for obj in response['Contents']:
            if repo_zip == obj['Key']:
                tags = s3.get_object_tagging(
                    Bucket=bucket, Key=obj['Key'])['TagSet']
                for tag in tags:
                    if tag['Key'] == 'latest_commit' and tag['Value'] == sha:
                        logger.debug(
                            'is_pr_synced({},{}) returned True'.format(
                                pr_number,
                                sha
                            ))
                        return True
    except Exception as e:
        logger.error(
            'is_pr_synced({},{}) Exception: {}'.format(
                pr_number,
                sha,
                e
            ))
        return False
    logger.debug(
        'is_pr_synced({},{}) returning False'.format(
            pr_number,
            sha
        ))
    return False


def lambda_handler(event, context):
    """
    Checks if repo for PRs and syncs open PRs (and commits) into an S3 bucket
    """
    open_pr_json = get_open_pull_requests()

    synced_prs = []
    for pr in open_pr_json:
        """
        Check if in S3
        If not in s3 get zip and place it there
        """
        logger.debug('Checking PR: {}'.format(pr['number']))
        branch_name = pr['head']['ref'].replace('refs/heads/', '')
        archive_url = pr['head']['repo']['archive_url'].replace(
            '{archive_format}',
            'zipball').replace(
            '{/ref}', '/' + branch_name
        )
        headers = {}
        if not is_pr_synced(pr['number'], pr['head']['sha']):
            r = requests.get(archive_url, headers=headers)
            archive_name = '/tmp/repo.zip'
            s3_object_key = '{}/repo.zip'.format(pr['number'])
            with open(archive_name, 'wb') as f:
                f.write(r.content)
            s3.upload_file(
                archive_name,
                bucket,
                s3_object_key
            )
            logger.debug('Copied zip file to s3')
            s3.put_object_tagging(
                Bucket=bucket,
                Key=s3_object_key,
                Tagging={
                    'TagSet': [
                        {
                            'Key': 'latest_commit',
                            'Value': pr['head']['sha']
                        },
                    ]
                }
            )
            synced_prs.append({
                'number': pr['number'],
                'title': pr['title'],
                'submitted_by': pr['user']['login'],
                'url': pr['url'],
                'html_url': pr['html_url'],
                'pr_repo': pr['head']['repo']['full_name'],
                'archive_url': pr['head']['repo']['archive_url'].replace(
                    '{archive_format}',
                    'zipball').replace(
                    '{/ref}', '/' + branch_name)
            })
    if synced_prs == []:
        logger.info('No updates')
    else:
        logger.info('The following PRs where updated in S3: {}'.format(
            synced_prs))
