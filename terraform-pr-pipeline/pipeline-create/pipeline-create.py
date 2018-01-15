import os
import logging
import re
import boto3
import requests

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
pac = os.environ['GITHUB_PAC']
github_api_url = os.environ['GITHUB_API_URL']
repo = os.environ['GITHUB_REPO_NAME']
bucket = os.environ['BUCKET_NAME']
project_name = os.environ['PROJECT_NAME']
code_build_image = os.environ['CODE_BUILD_IMAGE']
terraform_download_url = os.environ['TERRAFORM_DOWNLOAD_URL']
codebuild_service_role = os.environ['CODEBUILD_SERVICE_ROLE']
codepipeline_service_role = os.environ['CODEPIPELINE_SERVICE_ROLE']
kms_key = os.environ['KMS_KEY']


def pipeline_exists(pr_number):
    """Returns True if AWS CodePipeline pipeline exists"""
    try:
        codepipeline.get_pipeline(name='{}-terraform-pr-{}'.format(
            project_name,
            pr_number))
    except codepipeline.exceptions.PipelineNotFoundException:
        return False
    return True


def codebuild_project_exists(pr_number, name):
    """
    Returns True if AWS CodeBuild project exists
    """
    results = codebuild.batch_get_projects(names=[
        '{}-terraform-pr-{}-{}'.format(project_name, name, pr_number)
    ])
    if results['projectsNotFound'] == []:
        return True
    return False


def remove_list_duplicates(input_list):
    """Removes duplicates entries from list"""
    return list(dict.fromkeys(input_list))


def get_modified_directories(pr_number):
    """
    Returns a dict containing paths to the modified directories from the PR
    """
    # Get pull request info
    response = requests.get('https://api.github.com/repos/{}/pulls/{}'.format(
        repo,
        pr_number
    ))
    # Get Diffs
    diff_url = response.json()['diff_url']
    response = requests.get(diff_url)

    # Determine all counts of files modified
    expression = r'( b\/[^\s][^\\]*)+'
    files_modified = []
    for obj in re.finditer(expression, '{}'.format(response.content)):
        if '.tf' in obj.group(1):
            files_modified.append(obj.group(1)[3:])
    files_modified = remove_list_duplicates(files_modified)

    # Get DIRs (for terraform fmt)
    dirs = []
    test_dirs = []
    for file in files_modified:
        dir_only = file.split('/')[:-1]
        if dir_only == []:
            dirs.append('.')
            test_dirs.append('tests')
            continue
        dirs.append('/'.join(dir_only))
        if 'tests' in file:
            test_dirs.append('/'.join(dir_only))
        else:
            test_dirs.append(
                '{}/tests'.format(
                    '/'.join(dir_only)
                ))
    dirs = remove_list_duplicates(dirs)
    test_dirs = remove_list_duplicates(test_dirs)

    return {
        'dirs': dirs,
        'test_dirs': test_dirs
    }


def create_pipeline(pr_number):
    """
    Creates pipeline and codebuild resources
    """
    modified_dirs = get_modified_directories(pr_number)
    dirs = modified_dirs['dirs']
    test_dirs = modified_dirs['test_dirs']
    if not codebuild_project_exists(pr_number, 'fmt'):
        logger.info('Creating terraform-fmt codebuild project')
        with open('buildspec-terraform-fmt.yml', 'r') as buildspecfile:
            buildspec = buildspecfile.read()
        codebuild.create_project(
            name='{}-terraform-pr-fmt-{}'.format(project_name, pr_number),
            description='Checks if code is formatted',
            source={
                'type': 'CODEPIPELINE',
                'buildspec': buildspec,
            },
            artifacts={
                'type': 'CODEPIPELINE',
            },
            environment={
                'type': 'LINUX_CONTAINER',
                'image': code_build_image,
                'computeType': 'BUILD_GENERAL1_SMALL',
                'environmentVariables': [
                    {
                        'name': 'GITHUB_API_URL',
                        'value': github_api_url,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'GITHUB_PAC',
                        'value': pac,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'MODIFIED_DIRS',
                        'value': ' '.join(dirs),
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'MODIFIED_TEST_DIRS',
                        'value': ' '.join(test_dirs),
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'PR_NUMBER',
                        'value': pr_number,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO',
                        'value': repo.split('/')[1],
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO_NAME',
                        'value': repo.replace('/', '-'),
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO_OWNER',
                        'value': repo.split('/')[0],
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'S3_BUCKET',
                        'value': bucket,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'TERRAFORM_DOWNLOAD_URL',
                        'value': terraform_download_url,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'TF_IN_AUTOMATION',
                        'value': 'True',
                        'type': 'PLAINTEXT'
                    },
                ]
            },
            serviceRole=codebuild_service_role,
            timeoutInMinutes=5,
            encryptionKey=kms_key,
        )

    if not codebuild_project_exists(pr_number, 'terrascan'):
        logger.info('Creating terrascan codebuild project')
        with open('buildspec-terrascan.yml', 'r') as buildspecfile:
            buildspec = buildspecfile.read()
        codebuild.create_project(
            name='{}-terraform-pr-terrascan-{}'.format(
                project_name, pr_number),
            description='Runs terrascan against PR',
            source={
                'type': 'CODEPIPELINE',
                'buildspec': buildspec,
            },
            artifacts={
                'type': 'CODEPIPELINE',
            },
            environment={
                'type': 'LINUX_CONTAINER',
                'image': code_build_image,
                'computeType': 'BUILD_GENERAL1_SMALL',
                'environmentVariables': [
                    {
                        'name': 'GITHUB_API_URL',
                        'value': github_api_url,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'GITHUB_PAC',
                        'value': pac,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'MODIFIED_DIRS',
                        'value': ' '.join(dirs),
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'MODIFIED_TEST_DIRS',
                        'value': ' '.join(test_dirs),
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'PR_NUMBER',
                        'value': pr_number,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO',
                        'value': repo.split('/')[1],
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO_NAME',
                        'value': repo.replace('/', '-'),
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO_OWNER',
                        'value': repo.split('/')[0],
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'S3_BUCKET',
                        'value': bucket,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'TERRAFORM_DOWNLOAD_URL',
                        'value': terraform_download_url,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'TF_IN_AUTOMATION',
                        'value': 'True',
                        'type': 'PLAINTEXT'
                    },
                ]
            },
            serviceRole=codebuild_service_role,
            timeoutInMinutes=5,
            encryptionKey=kms_key,
        )

    if not codebuild_project_exists(pr_number, 'plan'):
        logger.info('Creating tfplan codebuild project')
        with open('buildspec-terraform-plan.yml', 'r') as buildspecfile:
            buildspec = buildspecfile.read()
        codebuild.create_project(
            name='{}-terraform-pr-plan-{}'.format(project_name, pr_number),
            description='Runs terraform plan against PR',
            source={
                'type': 'CODEPIPELINE',
                'buildspec': buildspec,
            },
            artifacts={
                'type': 'CODEPIPELINE',
            },
            environment={
                'type': 'LINUX_CONTAINER',
                'image': code_build_image,
                'computeType': 'BUILD_GENERAL1_SMALL',
                'environmentVariables': [
                    {
                        'name': 'GITHUB_API_URL',
                        'value': github_api_url,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'GITHUB_PAC',
                        'value': pac,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'MODIFIED_DIRS',
                        'value': ' '.join(dirs),
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'MODIFIED_TEST_DIRS',
                        'value': ' '.join(test_dirs),
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'PR_NUMBER',
                        'value': pr_number,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO',
                        'value': repo.split('/')[1],
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO_NAME',
                        'value': repo.replace('/', '-'),
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO_OWNER',
                        'value': repo.split('/')[0],
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'S3_BUCKET',
                        'value': bucket,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'TERRAFORM_DOWNLOAD_URL',
                        'value': terraform_download_url,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'TF_IN_AUTOMATION',
                        'value': 'True',
                        'type': 'PLAINTEXT'
                    },
                ]
            },
            serviceRole=codebuild_service_role,
            timeoutInMinutes=10,
            encryptionKey=kms_key,
        )

    logger.info('Creating pipeline')
    codepipeline.create_pipeline(
        pipeline={
            'name': '{}-terraform-pr-pipeline-{}'.format(
                project_name,
                pr_number),
            'roleArn': codepipeline_service_role,
            'artifactStore': {
                'type': 'S3',
                'location': bucket,
                'encryptionKey': {
                    'id': kms_key,
                    'type': 'KMS'
                }
            },
            'stages': [
                {
                    'name': 'receive-pr-source',
                    'actions': [
                        {
                            'name': 'pr-repo',
                            'actionTypeId': {
                                'category': 'Source',
                                'owner': 'AWS',
                                'provider': 'S3',
                                'version': '1'
                            },
                            'configuration': {
                                'S3Bucket': bucket,
                                'PollForSourceChanges': 'True',
                                'S3ObjectKey': '{}/repo.zip'.format(
                                    pr_number)
                            },
                            'outputArtifacts': [
                                {
                                    'name': 'source_zip'
                                },
                            ]
                        },
                    ]
                },
                {
                    'name': 'pull-request-tests',
                    'actions': [
                        {
                            'name': 'terraform-fmt',
                            'actionTypeId': {
                                'category': 'Test',
                                'owner': 'AWS',
                                'provider': 'CodeBuild',
                                'version': '1'
                            },
                            'configuration': {
                                'ProjectName': '{}-terraform-pr-fmt-{}'.format(
                                    project_name, pr_number)
                            },
                            'inputArtifacts': [
                                {
                                    'name': 'source_zip'
                                },
                            ]
                        },
                        {
                            'name': 'terrascan',
                            'actionTypeId': {
                                'category': 'Test',
                                'owner': 'AWS',
                                'provider': 'CodeBuild',
                                'version': '1'
                            },
                            'configuration': {
                                'ProjectName':
                                    '{}-terraform-pr-terrascan-{}'.format(
                                        project_name, pr_number)
                            },
                            'inputArtifacts': [
                                {
                                    'name': 'source_zip'
                                },
                            ]
                        },
                        {
                            'name': 'terraform-plan',
                            'actionTypeId': {
                                'category': 'Build',
                                'owner': 'AWS',
                                'provider': 'CodeBuild',
                                'version': '1'
                            },
                            'configuration': {
                                'ProjectName':
                                    '{}-terraform-pr-plan-{}'.format(
                                        project_name, pr_number)
                            },
                            'inputArtifacts': [
                                {
                                    'name': 'source_zip'
                                },
                            ]
                        }
                    ]
                }
            ]
        }
    )


def lambda_handler(event, context):
    """
    Creates pipeline when a new repo is uploaded to s3
    """
    pr_number = event['Records'][0]['s3']['object']['key'].split('/')[0]
    logger.info('Changes detected on PR #{}'.format(pr_number))

    if not pipeline_exists(pr_number):
        create_pipeline(pr_number)
