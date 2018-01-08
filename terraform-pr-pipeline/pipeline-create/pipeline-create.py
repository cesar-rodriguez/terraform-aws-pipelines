import os
import logging
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
codebuild = boto3.client('codebuild')

# Global vars
# pac = os.environ['GITHUB_PAC']
github_api_url = os.environ['GITHUB_API_URL']
repo = os.environ['GITHUB_REPO_NAME']
bucket = os.environ['BUCKET_NAME']
project_name = os.environ['PROJECT_NAME']
code_build_image = os.environ['CODE_BUILD_IMAGE']
terraform_download_url = os.environ['TERRAFORM_DOWNLOAD_URL']
codebuild_service_role = os.environ['CODEBUILD_SERVICE_ROLE']
codepipeline_service_role = os.environ['CODEPIPELINE_SERVICE_ROLE']


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
    """Returns True if AWS CodeBuild project exists"""
    results = codebuild.batch_get_projects(names=[
        '{}-terraform-pr-{}-{}'.format(project_name, name, pr_number)
    ])
    if results['projectsNotFound'] == []:
        return True
    return False


def create_pipeline(pr_number):
    """
    Creates pipeline and codebuild resources
    """
    if not codebuild_project_exists(pr_number, 'fmt'):
        logger.debug('Creating terraform-fmt codebuild project')
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
                        'name': 'TERRAFORM_DOWNLOAD_URL',
                        'value': terraform_download_url,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'TF_IN_AUTOMATION',
                        'value': 'True',
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO_NAME',
                        'value': repo.replace('/', '-'),
                        'type': 'PLAINTEXT'
                    }
                ]
            },
            serviceRole=codebuild_service_role,
            timeoutInMinutes=5,
        )

    if not codebuild_project_exists(pr_number, 'terrascan'):
        logger.debug('Creating terrascan codebuild project')
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
                        'name': 'TERRAFORM_DOWNLOAD_URL',
                        'value': terraform_download_url,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO_NAME',
                        'value': repo.replace('/', '-'),
                        'type': 'PLAINTEXT'
                    }
                ]
            },
            serviceRole=codebuild_service_role,
            timeoutInMinutes=5,
        )

    if not codebuild_project_exists(pr_number, 'plan'):
        logger.debug('Creating tfplan codebuild project')
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
                        'name': 'TERRAFORM_DOWNLOAD_URL',
                        'value': terraform_download_url,
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'TF_IN_AUTOMATION',
                        'value': 'True',
                        'type': 'PLAINTEXT'
                    },
                    {
                        'name': 'REPO_NAME',
                        'value': repo.replace('/', '-'),
                        'type': 'PLAINTEXT'
                    }
                ]
            },
            serviceRole=codebuild_service_role,
            timeoutInMinutes=10,
        )

    logger.debug('Creating pipeline')
    codepipeline.create_pipeline(
        pipeline={
            'name': '{}-terraform-pr-pipeline-{}'.format(
                project_name,
                pr_number),
            'roleArn': codepipeline_service_role,
            'artifactStore': {
                'type': 'S3',
                'location': bucket
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
                    'name': 'static-code-analysis',
                    'actions': [
                        {
                            'name': 'terraform-fmt',
                            'actionTypeId': {
                                'category': 'Test',
                                'owner': 'AWS',
                                'provider': 'CodeBuild',
                                'version': '1'
                            },
                            'runOrder': 1,
                            'configuration': {
                                'ProjectName': '{}-terraform-pr-fmt-{}'.format(
                                    project_name, pr_number)
                            },
                            'outputArtifacts': [
                                {
                                    'name': 'terraform_fmt'
                                },
                            ],
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
                            'runOrder': 1,
                            'configuration': {
                                'ProjectName':
                                    '{}-terraform-pr-terrascan-{}'.format(
                                        project_name, pr_number)
                            },
                            'outputArtifacts': [
                                {
                                    'name': 'terrascan'
                                },
                            ],
                            'inputArtifacts': [
                                {
                                    'name': 'source_zip'
                                },
                            ]
                        },
                        {
                            'name': 'post-results',
                            'actionTypeId': {
                                'category': 'Invoke',
                                'owner': 'AWS',
                                'provider': 'Lambda',
                                'version': '1'
                            },
                            'runOrder': 2,
                            'configuration': {
                                'FunctionName':
                                    '{}-post-comment'.format(
                                        project_name),
                                'UserParameters': pr_number
                            },
                            'inputArtifacts': [
                                {
                                    'name': 'terraform_fmt',
                                },
                                {
                                    'name': 'terrascan'
                                }
                            ]
                        }
                    ]
                },
                {
                    'name': 'terraform-plan',
                    'actions': [
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
                            'outputArtifacts': [
                                {
                                    'name': 'terraform_plan'
                                },
                            ],
                            'inputArtifacts': [
                                {
                                    'name': 'source_zip'
                                },
                            ]
                        },
                        {
                            'name': 'post-results',
                            'actionTypeId': {
                                'category': 'Invoke',
                                'owner': 'AWS',
                                'provider': 'Lambda',
                                'version': '1'
                            },
                            'runOrder': 2,
                            'configuration': {
                                'FunctionName':
                                    '{}-post-comment'.format(
                                        project_name),
                                'UserParameters': pr_number
                            },
                            'inputArtifacts': [
                                {
                                    'name': 'terraform_plan',
                                }
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
    logger.debug('Changes detected on PR #{}'.format(pr_number))

    if not pipeline_exists(pr_number):
        create_pipeline(pr_number)
