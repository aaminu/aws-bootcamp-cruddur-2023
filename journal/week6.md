# Week 6 — Deploying Containers
This week journal would detail the steps required to have tasks run in an AWS ECS cluster with using the Fargate launch type. These tasks would be placed behind an application load balancer (ALB) and accessed via a domain name hosted on Route53. The steps below show a consolidated approach from from all the mini build up.

## Route53, Hosted Zone, SSL Certs
Similar to Andrew, my registered domain name (aaminu.com) lives on another aws account. To make use of the same domain name, the following steps were followed:
1. Created a new hosted zone with the same naked domain as my registered domain name. The following setting was used. 
    - Domain name: aaminu.com
    - Description: A brief description
    - Type: Public hosted zone

2. The above created two records. I opened the NS record and copied out the name servers. I updated the name servers of my original registered domain. This change propagated under 60secs

3. To ensure the domain uses TLS/SSL, a certificated was created in AWS certificate manager. The following steps are required to get a certificate:
    - In the landing page, click on request
    - Certificate type: Request a public certificate
    - In the Domain names, I add the naked domain name and two levels of wildcard subdomain. One of which is **.cruddur.aaminu.com*. The would allow me use both *api.cruddur.aaminu.com & app.cruddur.aaminu.com* with the same certificate. 
    ![ns](./images/ns.png)
    - After clicking on created, I am redirected to the certifcated landing page. In there there's a button that allows one to created the required record in Route53, I clicked on it and created the record. This step took a while before the certificated changed to *Issued*. 
4. Back in the route53 hosted zone, one should find a CNAME record created.
5. In the application load balancer section, aliases would be created in the same hosted zone to point to the alb endpoint.


## CloudWatch Logs Preparation
We need to create a log group required later for task-definitions. In my case, I already had the log group, all I did was to adjust the retention policy via click-ops. To create a log group with a retention policy via CLI, the following can be used
```bash
aws logs create-log-group --log-group-name "<name>"
aws logs put-retention-policy --log-group-name "<name>" --retention-in-days <number-of-days>
```
In the process of cleaning up old logs, I realized an error in my post-confirmation-lambda. After inspecting, a fix was implemented and the affected part is shown in the screen short below:
![correct_lambda](./images/lambda_corrrect.png)


## Application Load Balancer and Target Groups
Since the goal is to have our ecs cluster and the services/tasks it contains sit behind a load balancer, the following was performed
1. Created a security group for the ALB. With this approach, the SG can be included in the  SG of other service's, thereby granting access:
    ```bash
    export ALB_SG=$(aws ec2 create-security-group \
      --group-name "cruddur-alb-sg" \
      --description "Security group for ALB" \
      --vpc-id $DEFAULT_VPC_ID \
      --query "GroupId" --output text)
    
    echo $ALB_SG
    ```
    Add ingress rules on port 80(Http) & 443(Https) for all sources by:

    ```bash
    aws ec2 authorize-security-group-ingress \
      --group-id $ALB_SG \
      --protocol tcp \
      --port 80 \
      --cidr 0.0.0.0/0

    aws ec2 authorize-security-group-ingress \
      --group-id $ALB_SG \
      --protocol tcp \
      --port 443 \
      --cidr 0.0.0.0/0
    ```
    One can inspect the above by navigating to EC2->Network & Security->Security Groups->cruddur-alb-sg

2. In the EC2 console page, I navigated to Target groups and created two targets group namely:
    - cruddur-backend-flask-tg. The specs of this target group are
        - Target type= IP
        - IP address type= IPV4
        - Protocol : Port = HTTP: 4567
        - Protocol version = HTTP1
        - Health check protocol = HTTP
        - Health check endpoint = /api/health-check
        - Selected the appropriate VPC and left everything else as defaults

    - cruddur-frontend-reactjs-tg. The specs of this target group are
        - Target type= IP
        - IP address type= IPV4
        - Protocol : Port = HTTP: 3000
        - Protocol version = HTTP1
        - Health check protocol = HTTP
        - Health check endpoint = /api/health-check
        - Selected the appropriate VPC and left everything else as defaults

3. Navigated to Load Balancers and created one with the following specifications:
    - Load balancer type: Application Load Balancer
    - Load balancer name: cruddur-alb
    - Scheme: Internet-facing
    - IP address type: IPV4
    - Used the default VPC and selected all the subnet available to me.
    - Selected the cruddur-alb-sg from the security group dropdown
    - Added One listener:
        - Protocol: HTTPS
        - Port: 443
        - Default action: Selected cruddur-frontend-reactjs-tg target group from the drop down
        - In the secure listener settings, selected the certificate created in ACM described in the previous chapter
    - Created the load balancer

4. Back in the load balance summary page, I selected the ALB created from above. I added an additional HTTP listener on port 80 and redirected it to HTTPS:443 with status code of *301 - Permanently moved*
    

5. I also edited the listener on port 443 to forward url paths of *api.cruddur.aaminu.com* to the cruddur-backend-flask-tg target group. The can be done as shown in the picture below:
  ![edit1](./images/list-edit1.png)
  ![edit2](./images/list-edit2.png)
  ![edit3](./images/list-edit3.png)

6. As a final step to have the alias pointing to the ALB, I created two record type aliases in route53 underneath the *aaminu.com* hosted zone, Both were pointed to the ALB:
  ![aliases](./images/aliases.png)
  The two aliases are depicted below:
  ![aliases2](./images/alias2.png)
    - The *app.cruddur.aaminu.com* points to the frontend webpage
    - The *api.cruddur.aaminu.com* points to the backend api



## **Building Production FE & BE Containers, ECR Usage**
This section details the steps taken to build and push production versions of containers currently used in the development. Before getting started with pushing containers to ECR, I had to login via the CLI by:
```bash
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"
```

### **Backend Flask Container Building** 
1. To avoid any problems one can encounter with dockerhub during builds, the base python image is pulled from dockerhub, built, tagged and pushed to own registry on ecr following the steps detailed below:
    - Made a repo to hold the image:
      ```bash
      aws ecr create-repository \
        --repository-name "cruddur-python" \
        --image-tag-mutability MUTABLE
      ```
    - Exported the url to my environment variables and persisted it my gitpod workspace:
      ```bash
      export ECR_PYTHON_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/cruddur-python"
      gp env ECR_PYTHON_URL=$ECR_PYTHON_URL
      ```
    - I pulled the image from dockerhub, tagged it, and proceeded to push it to the ECR repo from above:
      ```bash
      docker pull python:3.10-slim-buster
      docker tag python:3.10-slim-buster $ECR_PYTHON_URL:3.10-slim-buster
      docker push $ECR_PYTHON_URL:3.10-slim-buster
      ```

2. Updated the current [Dockerfile](../backend-flask/Dockerfile) to use my python ecr image from 1. above by:
    ```docker
    ARG image_name

    FROM ${image_name}

    RUN apt-get update && apt-get install -y curl

    WORKDIR /backend-flask

    COPY requirements.txt requirements.txt
    RUN pip3 install -r requirements.txt

    COPY . .

    EXPOSE ${PORT}
    CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567", "--debug"]
    ```
3. In the [docker-compose.yml](../docker-compose.yml) file, I updated the backend task to use this image as an argument for building:
    ```yaml
    version: "3.8"
    services:
      backend-flask: 
        environment:
          # Environment variables...........
        build: 
          context: ./backend-flask
          args:
            image_name: "${ECR_PYTHON_URL}:3.10-slim-buster" # <---- ECR Image Here
        ports:
          - "4567:4567"
        volumes:
          - ./backend-flask:/backend-flask
    ```
    The above was tested using *Docker compose up*

4. In preparation of building a production docker file. The [bin](../bin/) directory was refactored out of the [backend-flask](../backend-flask/) directory.
5. In [app.py](../backend-flask/app.py), a health check endpoint was added as part of the routes:
    ```python
    @app.route('/api/health-check')
    def health_check():
        return {'success': True}, 200
    ```
6. Created a new [bin](../backend-flask/bin) directory within the [backend-flask](../backend-flask/) directory. In there, I created a [flask](../backend-flask/bin/flask/) directory and placed a script called [health-check](../backend-flask/bin/flask/health-check). This script would be used to check the health of our web-server when deployed to ECS. The content of script is shown below:
    ```bash
    #!/usr/bin/env python3

    import urllib.request

    try:
        response = urllib.request.urlopen('http://localhost:4567/api/health-check')
        if response.getcode() == 200:
            print("[Okay]: Flask server is running")
            exit(0)
        else:
            print("[Error]: Flask server is not running")
            exit(1)
    except Exception as e:
        print("[Exception]: ", e)
        exit(0)
    ```
    I modified the permissions to this script by ```chmod 744 backend-flask/bin/flask/health-check ``` in the terminal.
7. Next was to create the [Dockerfile.prod](../backend-flask/Dockerfile.prod) which disables debugging and logging. The contents is shown below:

    ```docker
      ARG image_name

      FROM ${image_name}

      RUN apt-get update && apt-get install -y curl

      WORKDIR /backend-flask

      COPY requirements.txt requirements.txt
      RUN pip3 install -r requirements.txt

      COPY . .

      EXPOSE ${PORT}
      CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567", "--no-debug", "--no-debugger", "--no-reload"]
      ```
8. I built the dockerfile from above, tagged and pushed it to its own repo. Part of the commands shown below created a repo for the backend-flask image:
    ```bash
    aws ecr create-repository \
      --repository-name backend-flask \
      --image-tag-mutability MUTABLE

    export ECR_BACKEND_FLASK_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/backend-flask"
    gp env ECR_BACKEND_FLASK_URL=$ECR_BACKEND_FLASK_URL

    cd backend-flask/
    docker build -t backend-flask --build-arg image_name=$ECR_PYTHON_URL:3.10-slim-buster -f "Dockerfile.prod" .
    docker tag backend-flask:latest $ECR_BACKEND_FLASK_URL:latest
    docker push $ECR_BACKEND_FLASK_URL:latest 
    ```

### **Frontend React-JS Container Building** 
1. First stop was to navigate to the [/frontend-react-js](../frontend-react-js/) directory and create a [Dockerfile.prod](../frontend-react-js/Dockerfile.prod) file with content:
    ```docker
    # Base Image ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    FROM node:16.18 AS build

    ARG REACT_APP_BACKEND_URL
    ARG REACT_APP_AWS_PROJECT_REGION
    ARG REACT_APP_AWS_COGNITO_REGION
    ARG REACT_APP_AWS_USER_POOLS_ID
    ARG REACT_APP_CLIENT_ID

    ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
    ENV REACT_APP_AWS_PROJECT_REGION=$REACT_APP_AWS_PROJECT_REGION
    ENV REACT_APP_AWS_COGNITO_REGION=$REACT_APP_AWS_COGNITO_REGION
    ENV REACT_APP_AWS_USER_POOLS_ID=$REACT_APP_AWS_USER_POOLS_ID
    ENV REACT_APP_CLIENT_ID=$REACT_APP_CLIENT_ID

    COPY . ./frontend-react-js
    WORKDIR /frontend-react-js
    RUN npm install
    RUN npm run build

    # New Base Image ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    FROM nginx:1.23.3-alpine

    # --from build is coming from the Base Image
    COPY --from=build /frontend-react-js/build /usr/share/nginx/html
    COPY --from=build /frontend-react-js/nginx.conf /etc/nginx/nginx.conf

    EXPOSE 3000
    ```
2. In the same direction, I created a [nginx.conf](../frontend-react-js/nginx.conf) configuration file. Please file for contents.

3. I had to also create a repo in ECR that'll hold the frontend image and also exported the url to my env variables:
    ```bash
    aws ecr create-repository \
      --repository-name frontend-react-js \
      --image-tag-mutability MUTABLE

    export ECR_FRONTEND_REACT_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/frontend-react-js"

    gp env ECR_FRONTEND_REACT_URL=$ECR_FRONTEND_REACT_URL
    ```
4. While still in the frontend [/frontend-react-js](../frontend-react-js/) directory





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

db/test
flask/health-check





ECS
aws ecs create-cluster \
--cluster-name cruddur \
--service-connect-defaults namespace=cruddur





backend-flask


cd  backend
update in flask Dockerfile image_name
comment out x-ray in app.py and other services

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



fix token refresh and replace in all required location