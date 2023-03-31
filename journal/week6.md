# Week 6 — Deploying Containers

db/test
flask/health check

cloud watchlog
aws logs create-log-group --log-group-name "/cruddur/fargate-cluster"
aws logs put-retention-policy --log-group-name "/cruddur/fargate-cluster" --retention-in-days 3

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
docker build -t backend-flask --build-arg image_name=$ECR_PYTHON_URL:3.10-slim-buster .
docker tag backend-flask:latest $ECR_BACKEND_FLASK_URL:latest
docker push $ECR_BACKEND_FLASK_URL:latest
update in docker compose

front-end
aws ecr create-repository \
  --repository-name frontend-react-js \
  --image-tag-mutability MUTABLE

export ECR_FRONTEND_REACT_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/frontend-react-js"
echo $ECR_FRONTEND_REACT_URL