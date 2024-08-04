deploy:
	chalice deploy

create-stack:
	aws cloudformation create-stack --stack-name ragtube-stack --template-body file://ragtube-stack.yaml

update-stack:
	aws cloudformation update-stack --stack-name ragtube-stack --template-body file://ragtube-stack.yaml

delete-stack:
	aws cloudformation delete-stack --stack-name ragtube-stack

check-stack:
	aws cloudformation describe-stacks --stack-name ragtube-stack

test-helper:
	@set -a; source ./local.env; python ./tests/test_helper.py

test-integration:
	@set -a; source ./local.env; python ./tests/test_integration.py



