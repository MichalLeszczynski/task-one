#!/bin/bash

aws s3 mb s3://mleszczynsk-cloudformation-templates
aws s3 cp internal-stack.yaml.j2 s3://mleszczynsk-cloudformation-templates/functions/internal-stack.yaml.j2
aws s3 cp main.py s3://mleszczynsk-cloudformation-templates/functions/main.py


# aws cloudformation create-stack \
#   --stack-name myteststack3 \
#   --template-body file://external-stack.yaml \
#   --parameters file://parameters.json --capabilities CAPABILITY_NAMED_IAM

aws cloudformation create-stack \
  --stack-name myteststack6 \
  --template-body file://external-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# aws cloudformation delete-stack --stack-name myteststack


aws cloudformation package \
  --template ./external-stack.yaml \
  --s3-bucket mleszczynsk-cloudformation-templates \
  --output-template-file packaged-stack.yaml


aws cloudformation deploy --template-file ./packaged-stack.yaml --stack-name myteststack8 --capabilities CAPABILITY_NAMED_IAM


pip install --target ./lambda_function -r ./lambda_function/requirements.txt
zip -r ./lambda_function/modules-package.zip ./package
