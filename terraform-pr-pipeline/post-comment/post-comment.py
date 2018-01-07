import os
import logging
from io import BytesIO
import zipfile
import boto3

# Configuring logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.handlers[0].setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
))
logging.getLogger('boto3').setLevel(logging.ERROR)
logging.getLogger('botocore').setLevel(logging.ERROR)

# Boto clients
codepipeline = boto3.client('codepipeline')
s3 = boto3.resource('s3')

# Global vars
# pac = os.environ['GITHUB_PAC']
github_api_url = os.environ['GITHUB_API_URL']
repo = os.environ['GITHUB_REPO_NAME']


def lambda_handler(event, context):
    """
    Posts a comment to GitHub with test results
    """
    logger.debug('event: {}'.format(event))

    logger.debug('Getting input artifacts')

    for artifact in event['CodePipeline.job']['data']['inputArtifacts']:
        logger.debug('Artifact name: {}'.format(artifact['name']))
        bucket = s3.Bucket(artifact['location']['s3Location']['bucketName'])
        obj = bucket.Object(artifact['location']['s3Location']['objectKey'])
        with BytesIO(obj.get()["Body"].read()) as tf:
            tf.seek(0)
            with zipfile.ZipFile(tf, mode='r') as zipf:
                if 'terraform-fmt-result.txt' in zipf.namelist():
                    with zipf.open('terraform-fmt-result.txt') as results:
                        fmt_results = results.read()
                        if b'' == fmt_results:
                            print('All files formatted')
                        else:
                            print('Files are not formatted: {}'.format(
                                fmt_results))
                if 'plan.log' in zipf.namelist():
                    with zipf.open('plan.log') as results:
                        tf_plan = results.read()
                        print(tf_plan)

    job_id = event['CodePipeline.job']['id']
    logger.debug('Job ID: {}'.format(job_id))

    response = codepipeline.put_job_success_result(
        jobId=job_id,
    )
    logger.debug('response: {}'.format(response))
