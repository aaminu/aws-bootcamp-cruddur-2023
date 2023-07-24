# Week X — Clean Up

## Sync Tool for Static Website Hosting

Setting up the required tool responsible for syncing the static file locted in the S3 Bucket which serves as an origin for the cloudfront distribution, the follow steps were take:

1. Created a [script](../bin/frontend/static-build) to build the static files from the frontend component. Changes were made to the necessary parameters e.g.`REACT_APP_BACKEND_URL`, `REACT_APP_AWS_USER_POOLS_ID`, and `REACT_APP_CLIENT_ID`:
    ```bash
    #! /usr/bin/bash -e 

    CYAN='\033[1;36m'
    NO_COLOR='\033[0m'
    LABEL="Frontend Static Build"
    printf "${CYAN}== ${LABEL}===${NO_COLOR}\n"

    current_file_path=`realpath $0`
    bin_dir=`dirname $(dirname $current_file_path)`
    base_dir=`dirname $bin_dir`
    FRONTEND_REACT_JS_PATH="$base_dir/frontend-react-js"

    echo $FRONTEND_REACT_JS_PATH

    REACT_APP_BACKEND_URL="https://api.cruddur.aaminu.com" \
    REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
    REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
    REACT_APP_AWS_USER_POOLS_ID="$AWS_USER_POOLS_ID" \
    REACT_APP_CLIENT_ID="$COGNITO_APP_CLIENT_ID" \
    npm run build
    ```
2. Changed the permission of the script to allow for it to be executable. To use the script as a standalone, one has to firstly navigate to the [frontend-react-js](../frontend-react-js/) directory in the commandline before executing the script

3. Created a [sync](../bin/frontend/sync) script for the s3 contnent syncing. Changed the permissions to allow executability. To make use of the script, certain installed module and env files are needed, they are detailed in 4, and 5 below:

4. In the commandline, installed aws_s3_website_sync and dotenv by 
    ```bash
    gem install aws_s3_website_sync
    gem install dotenv
    ```
    I also appended both commands to a gitpod task in [.gitpod.yml](../.gitpod.yml)

5. In [erb/](../erb/) directory, I created a new env.erb file ([sync.env.erb](../erb/sync.env.erb)) with the required env vars. In the [bin/frontend/generate-env](../bin/frontend/generate-env) script, I appended the commands required to generate the final sync.env file. I ran the [bin/frontend/generate-env](../bin/frontend/generate-env) in the command line.

6. With everything setup above, I ran the [sync](../bin/frontend/sync) script and the ouput can be seen below:

    ![sync](./images/sync-tool.png)
