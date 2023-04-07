# Week 6 — Deploying Containers

db/test
flask/health-check

cloud watchlog (already have, just change rentention)
aws logs create-log-group --log-group-name "cruddur"
aws logs put-retention-policy --log-group-name "cruddur" --retention-in-days 3

correction for post-confirmation-lambda

ECS
aws ecs create-cluster \
--cluster-name cruddur \
--service-connect-defaults namespace=cruddur

Make base images for python and react to avoid docker hub as a point of failure
aws ecr create-repository \
  --repository-name cruddur-python \
  --image-tag-mutability MUTABLE

login
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"

export ECR_PYTHON_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/cruddur-python
docker pull python:3.10-slim-buster
docker tag python:3.10-slim-buster $ECR_PYTHON_URL:3.10-slim-buster
docker push $ECR_PYTHON_URL:3.10-slim-buster


aws ecr create-repository \
  --repository-name cruddur-nodejs \
  --image-tag-mutability MUTABLE
export ECR_NODE_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/cruddur-nodejs
docker pull node:16.18
docker tag node:16.18 $ECR_NODE_URL:16.18
docker push $ECR_NODE_URL:16.18


backend-flask
aws ecr create-repository \
  --repository-name backend-flask \
  --image-tag-mutability MUTABLE

export ECR_BACKEND_FLASK_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/backend-flask"
gp env ECR_BACKEND_FLASK_URL=$ECR_BACKEND_FLASK_URL
cd  backend
update in flask Dockerfile image_name
comment out x-ray in app.py and other services
docker build -t backend-flask --build-arg image_name=$ECR_PYTHON_URL:3.10-slim-buster .
docker tag backend-flask:latest $ECR_BACKEND_FLASK_URL:latest
docker push $ECR_BACKEND_FLASK_URL:latest
update in docker compose

System Manager to keep sensitive parameters in parameter store
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/AWS_ACCESS_KEY_ID" --value $AWS_ACCESS_KEY_ID
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/AWS_SECRET_ACCESS_KEY" --value $AWS_SECRET_ACCESS_KEY
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/CONNECTION_URL" --value $PROD_CONNECTION_URL
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/ROLLBAR_ACCESS_TOKEN" --value $ROLLBAR_ACCESS_TOKEN
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/OTEL_EXPORTER_OTLP_HEADERS" --value "x-honeycomb-team=$HONEYCOMB_API_KEY"



Before starting out in ECS: 
create Service execution role
- Create a role 
aws iam create-role \    
--role-name CruddurServiceExecutionRole  \   
--assume-role-policy-document file://aws/policies/service-assume-role-execution-policy.json

-attach a service policy that allows it access ssm for parameters
aws iam put-role-policy \
  --policy-name CruddurServiceExecutionPolicy \
  --role-name CruddurServiceExecutionRole \
  --policy-document file://aws/policies/service-execution-policy.json
"


create task role 
- Create a role 
aws iam create-role \
--role-name CruddurTaskRole \
--assume-role-policy-document file://aws/policies/task-assume-role-execution-policy.json

-attach a service policy that allows it access ssm
aws iam put-role-policy \
  --policy-name CruddurTaskPolicy \
  --role-name CruddurTaskRole \
  --policy-document file://aws/policies/task-execution-policy.json


- Allow CloudWatch Access for logging
aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess --role-name CruddurTaskRole

- Allow Xray Deamon
aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess --role-name CruddurTaskRole


Create task-definitions
In the file make sure the names match wat was in the docker compose file 
aws ecs register-task-definition --cli-input-json file://aws/task-definitions/backend-flask.json

export VPC and subnet groups
export DEFAULT_VPC_ID=$(aws ec2 describe-vpcs \
--filters "Name=isDefault, Values=true" \
--query "Vpcs[0].VpcId" \
--output text)

echo $DEFAULT_VPC_ID

export DEFAULT_SUBNET_IDS=$(aws ec2 describe-subnets  \
 --filters Name=vpc-id,Values=$DEFAULT_VPC_ID \
 --query 'Subnets[*].SubnetId' \
 --output json | jq -r 'join(",")')
echo $DEFAULT_SUBNET_IDS

export CRUD_SERVICE_SG=$(aws ec2 create-security-group \
  --group-name "crud-srv-sg" \
  --description "Security group for Cruddur services on ECS" \
  --vpc-id $DEFAULT_VPC_ID \
  --query "GroupId" --output text)
echo $CRUD_SERVICE_SG



aws ec2 authorize-security-group-ingress \
  --group-id $CRUD_SERVICE_SG \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0


create target groups and alb before creting services
Create a service is cruddr cluster and check it is running using cli from aws/json
aws ecs create-service --cli-input-json file://aws/json/service-backend-flask.json


Install session manager
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb

session-manager-plugin

connect to the container by:
aws ecs execute-command  \
--region $AWS_DEFAULT_REGION \
--cluster cruddur \
--task 5745c1c6a87c49d9937440451b726ddf \
--container backend-flask \
--command "/bin/bash" \
--interactive



front-end
aws ecr create-repository \
  --repository-name frontend-react-js \
  --image-tag-mutability MUTABLE

export ECR_FRONTEND_REACT_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/frontend-react-js"
echo $ECR_FRONTEND_REACT_URL

docker build \
--build-arg REACT_APP_BACKEND_URL="$BACKEND_ALB_URL" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="$AWS_USER_POOLS_ID" \
--build-arg REACT_APP_CLIENT_ID="$COGNITO_APP_CLIENT_ID" \
-t frontend-react-js \
-f Dockerfile.prod .

docker tag frontend-react-js:latest $ECR_FRONTEND_REACT_URL:latest
docker push $ECR_FRONTEND_REACT_URL:latest
update in docker compose

configure security groups

aws ecs register-task-definition --cli-input-json file://aws/task-definitions/frontend-react-js.json

aws ecs create-service --cli-input-json file://aws/json/service-frontend-react-js.json


Do all the route53 and sg stuffs (populate this later)
export BAckend domain name

docker build \
--build-arg REACT_APP_BACKEND_URL="https://$BACKEND_DOMAIN_URL" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="$AWS_USER_POOLS_ID" \
--build-arg REACT_APP_CLIENT_ID="$COGNITO_APP_CLIENT_ID" \
-t frontend-react-js \
-f Dockerfile.prod .

docker tag frontend-react-js:latest $ECR_FRONTEND_REACT_URL:latest
docker push $ECR_FRONTEND_REACT_URL:latest