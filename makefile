# all:
# 	find /lambda_function -type d -exec rm -rf '{}' \;

STACKNAME="myteststack25"
BUCKETNAME="mleszczynsk-cloudformation-templates"

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

recreate: destroy
	make deploy

destroy: 
	aws cloudformation delete-stack --stack-name $(STACKNAME)

cleanup: 
	find ./lambda_function/. -type d -exec rm -rf '{}' \;

	# aws s3 rb $(BUCKETNAME)