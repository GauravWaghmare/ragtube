deploy: package
	aws cloudformation package --template-file out/sam.json --s3-bucket ragtube-stack-artifactbucket-pkb6vjtvuumg --output-template-file out/packaged-template.json
	aws cloudformation deploy --template-file out/packaged-template.json --stack-name ragtube --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND

package:
	chalice package --stage dev out/

create-stack:
	aws cloudformation create-stack --stack-name ragtube-stack --template-body file://ragtube-stack.yaml --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND

update-stack:
	aws cloudformation update-stack --stack-name ragtube-stack --template-body file://ragtube-stack.yaml --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND

delete-stack:
	aws cloudformation delete-stack --stack-name ragtube-stack

check-stack:
	aws cloudformation describe-stacks --stack-name ragtube-stack

test-helper:
	@set -a; source ./local.env; python ./tests/test_helper.py

test-integration:
	@set -a; source ./local.env; python ./tests/test_integration.py



