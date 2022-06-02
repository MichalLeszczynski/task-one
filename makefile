
STACKNAME=myteststack25
BUCKETNAME=mleszczynsk-cloudformation-templates

deploy: package
	aws cloudformation deploy --template-file ./packaged-stack.yaml --stack-name $(STACKNAME) --capabilities CAPABILITY_NAMED_IAM

package: bucket
	pip install --target ./lambda_function -r ./lambda_function/requirements.txt
	aws cloudformation package \
		--template ./external-stack.yaml \
		--s3-bucket $(BUCKETNAME) \
		--output-template-file packaged-stack.yaml

bucket: 
	aws s3 mb s3://mleszczynsk-cloudformation-templates || true

destroy: 
	aws cloudformation delete-stack --stack-name $(STACKNAME)

cleanup: destroy
	rm -rf lambda_function/*/
	aws s3 rm s3://$(BUCKETNAME) --recursive
	aws s3 rb s3://$(BUCKETNAME)

test: output
	awscurl -X POST --service lambda --region eu-central-1 $(shell cat url.txt) 

output:
	aws cloudformation describe-stacks --query 'Stacks[?StackName==`myteststack25`].Outputs[0][?OutputKey==`FunctionUrl`].OutputValue' --output=text > url.txt
