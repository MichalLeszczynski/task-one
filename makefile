
STACKNAME=mlesz-lambda-stack
BUCKETNAME=mlesz-cloudformation-templates
REGION=eu-central-1

deploy: package
	aws --region $(REGION) \
		cloudformation deploy \
		--template-file ./packaged-stack.yaml \
		--stack-name $(STACKNAME) \
		--capabilities CAPABILITY_NAMED_IAM

package: bucket
	pip install --target ./lambda_function -r ./lambda_function/requirements.txt
	aws --region $(REGION) \
		cloudformation package \
		--template ./external-stack.yaml \
		--s3-bucket $(BUCKETNAME) \
		--output-template-file packaged-stack.yaml

bucket: 
	aws --region $(REGION) s3 mb s3://$(BUCKETNAME) || true

destroy: 
	aws --region $(REGION) cloudformation delete-stack --stack-name $(STACKNAME)

cleanup: destroy
	rm -rf lambda_function/*/
	aws --region $(REGION) s3 rm s3://$(BUCKETNAME) --recursive
	aws --region $(REGION) s3 rb s3://$(BUCKETNAME)

deploy_payload: lambda_url_output
	awscurl -X POST --service lambda --region $(REGION) -H 'Content-Type: application/json' --data '$(shell cat create_payload.json | jq  -c)' $(shell cat url.txt) -v

delete_payload: lambda_url_output
	awscurl -X POST --service lambda --region $(REGION) -H 'Content-Type: application/json' --data '$(shell cat delete_payload.json | jq  -c)' $(shell cat url.txt) -v

lambda_url_output:
	aws --region $(REGION) \
	cloudformation describe-stacks \
	--query 'Stacks[?StackName==`$(STACKNAME)`].Outputs[0][?OutputKey==`FunctionUrl`].OutputValue' \
	--output=text > url.txt # hackish output indexing

payload_key_id_output:
	aws --region $(REGION) \
		cloudformation describe-stacks \
		--query 'Stacks[?StackName==`mlesz-ec2-stack`].Outputs[0][?OutputKey==`KeyPairId`].OutputValue' \
		--output text > key_pair_id.txt # hackish output indexing

get-keys: payload_key_id_output
	echo "`aws ssm get-parameter --name /ec2/keypair/$(shell cat key_pair_id.txt) --region eu-central-1 --with-decryption | jq .Parameter.Value | cut -d '\"' -f 2`" > key.pem
	chmod 600 key.pem

payload_public_dns_output:
	aws --region $(REGION) \
		cloudformation describe-stacks \
		--query 'Stacks[?StackName==`mlesz-ec2-stack`].Outputs[1][?OutputKey==`InstanceDnsName`].OutputValue' \
		--output text > public_dns.txt

login: get-keys payload_public_dns_output
	ssh -i ./key.pem ec2-user@$(shell cat public_dns.txt)