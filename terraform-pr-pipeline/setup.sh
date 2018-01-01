 #!/bin/bash

set -ex

echo "Empties directory"
rm -rf .lambda-zip/

echo "Makes new directories for lambda resources"
mkdir -p .lambda-zip/pipeline-create-resources
mkdir -p .lambda-zip/pipeline-delete-resources
mkdir -p .lambda-zip/poller-create-resources
mkdir -p .lambda-zip/poller-delete-resources

echo "Installing dependencies"
pip install --target=.lambda-zip/pipeline-create-resources -r pipeline-create/requirements.txt
#pip install --target=.lambda-zip/pipeline-delete-resources -r pipeline-delete/requirements.txt
pip install --target=.lambda-zip/poller-create-resources -r poller-create/requirements.txt
pip install --target=.lambda-zip/poller-delete-resources -r poller-delete/requirements.txt

echo "Copying function"
cp -R pipeline-create/pipeline-create.py .lambda-zip/pipeline-create-resources/.
#cp -R pipeline-delete/pipeline-delete.py .lambda-zip/pipeline-delete-resources/.
cp -R poller-create/poller-create.py .lambda-zip/poller-create-resources/.
cp -R poller-delete/poller-delete.py .lambda-zip/poller-delete-resources/.

echo "Creating zip files"
pushd .lambda-zip/pipeline-create-resources/ && zip -r ../pipeline-create.zip .
popd
#pushd .lambda-zip/pipeline-delete-resources/ && zip -r ../pipeline-delete.zip .
#popd
pushd .lambda-zip/poller-create-resources/ && zip -r ../poller-create.zip .
popd
pushd .lambda-zip/poller-delete-resources/ && zip -r ../poller-delete.zip .
popd
