# Week 4 — Postgres and RDS

## **Required Homework** 

### **Create RDS Postgres Instance**
To create an RDS instance running a postgres engine while also trying to maintain security best practices, the following approach was employed:
1. The master-username, master-user-password, and port was generated set:
    ```bash
    export POSTGRES_MASTER_USERNAME="<my-master-username>"
    gp env POSTGRES_MASTER_USERNAME=$POSTGRES_MASTER_USERNAME
    export POSTGRES_MASTER_PASSWORD="<my-master-password>"
    gp env POSTGRES_MASTER_PASSWORD=$POSTGRES_MASTER_PASSWORD
    export POSTGRES_PORT="<my-port>"
    gp env POSTGRES_PORT=$POSTGRES_PORT
    ```
2. To create a new instance in aws rds with our default aws region, the following command was run in the same terminal as above:
    ```bash
    $ aws rds create-db-instance \
      --db-instance-identifier cruddur-db-instance \
      --db-instance-class db.t3.micro \
      --engine postgres \
      --engine-version  14.6 \
      --master-username ${POSTGRES_MASTER_USERNAME} \
      --master-user-password ${POSTGRES_MASTER_PASSWORD} \
      --allocated-storage 20 \
      --availability-zone "${AWS_DEFAULT_REGION}a" \
      --backup-retention-period 0 \
      --port ${POSTGRES_PORT} \
      --no-multi-az \
      --db-name cruddur \
      --storage-type gp2 \
      --publicly-accessible \
      --storage-encrypted \
      --enable-performance-insights \
      --performance-insights-retention-period 7 \
      --no-deletion-protection
    ```
3. To ensure having the right url to the just created RDS instance, a connection link in the form of ```postgresql://[username[:password]@][netloc][:port][/dbname][?param1=value1&...]```is exported as an environment key by grabbing the endpoint name from aws rds instance and do the following:
    ```bash
    export PROD_DB_ENDPOINT="<my-endpoint>"
    gp env PROD_DB_ENDPOINT=$PROD_DB_ENDPOINT 
    export PROD_CONNECTION_URL = "postgresql://${POSTGRES_MASTER_USERNAME}:${POSTGRES_MASTER_PASSWORD}@${PROD_DB_ENDPOINT}:${POSTGRES_PORT}/cruddur"
    gp env PROD_CONNECTION_URL=$PROD_CONNECTION_URL
    ```
4. Accessing the local postgres container running, we need a similar link set in the environment:
    ```bash
    export CONNECTION_URL="postgresql://postgres:password@localhost:5432/cruddur"
    gp env CONNECTION_URL=$CONNECTION_URL
    ```
5. The link above does work with wheen the backend container tries to communicate with the postgres container, to fix that, a variation of 4. above is used and set:
    ```bash
    export CONNECTION_LOCAL_DOCKER_URL="postgresql://postgres:password@db:5432/cruddur"
    gp env CONNECTION_LOCAL_DOCKER_URL=$CONNECTION_LOCAL_DOCKER_URL
    ```
    the *netloc* from the postgres link format described in 3. above is replaces with name of the container used in the [docker-compose.yml](../docker-compose.yml) file. In my case that container is named *db*

6. Connecting to the aws RDS via the terminal can done by:
    ```bash
    psql $PROD_CONNECTION_URL

    ```
7. See below for result:

    ![db-prod](./images/db-prod.png)

### **Bash scripting for Database Operation and SQL files**
Various bash scripts were written and can all be found in the [/backend-flask/bin](../backend-flask/bin/) directory. Each one performs a specific functions. The following are some of the good to know:
1. Each script must start with  ```#! usr/bun/bash```

2. To ensure each script is executable, one can do batch permission modification by running the following command in the terminal while in the backend-flask directory:
    ```bash
    chmod 744 bin/db-*
    ```
3. For scripts that need to know their current parent directory irrespective of where they are called in the terminal, the following was used:
    ```bash
    current_file_path=`realpath $0`
    file_parent_dir=`dirname $(dirname $current_file_path)`
    ```
  This ensures in our case that ```file_parent_dir=/workspace/aws-bootcamp-cruddur-2023/backend-flask```at all times.

4. To allow for conditional execution, the following was added:
    ```bash
    if [ "$1" = "prod" ]; then
    echo "using production url"
    CON_URL=$PROD_CONNECTION_URL
    else
        CON_URL=$CONNECTION_URL
    fi
    ```

5. Also two sql files can be found in the [/backend-flask/bin](../backend-flask/db/) directory. The [schema.sql](../backend-flask/db/schema.sql) provides the tables model for the database cruddur and [seed.sql](../backend-flask/db/seed.sql) contains manually generated data for testing.

6. A picture of a test can be seen below of running the [db-setup](../backend-flask/bin/db-setup) bash script on a fresh postgres container:

    ![local-db-setup](./images/db-local-seed.png)

7. Inspection of the database showed:

    ![local-db-inners](./images/db-local-inners.png)

8. To allow connection fromm our workspace to the aws rds instance, a script [rds-update-sg-rule](../backend-flask/bin/rds-update-sg-rule) is created. This requires the following environment keys to be set *DB_SG_RULE_ID* and *DB_SG_ID*
  - The *DB_SG_ID* is the security group id of the security group attached to the rds instance
  - The *DB_SG_RULE_ID* is rule id contained in the above

9. Since the workspace is ephemeral, we need to set it at startup of every new workspace, the following was added to the postgres task in [.gitpod.yml](../.gitpod.yml) file:
    ```yaml
    command: |
      export GITPOD_IP=$(curl ifconfig.me)
      source "$THEIA_WORKSPACE_ROOT/backend-flask/bin/rds-update-sg-rule"
    ```

### **Install Postgres Driver in Backend Application and Connecting to Local RDS Instance**
1. We need the *psycopg* library as a driver for connecting to the postgres container. The following was added to the [requirements.txt](../backend-flask/requirements.txt) file
    ```txt  
    psycopg[binary]
    psycopg[pool]
    ```
2. In the [/backend-flask/lib](../backend-flask/lib/) directory, a file module called [db.py](../backend-flask/lib/db.py) is created and populated with:
    ```python
    from psycopg_pool import ConnectionPool
    import os

    # Wrap query and ensure object result is returned as json
    def query_wrap_object(template):
      sql = f"""
      (SELECT COALESCE(row_to_json(object_row),'{{}}'::json) FROM (
      {template}
      ) object_row);
      """
      return sql

    #Wrap query and ensure array result is returned as json
    def query_wrap_array(template):
      sql = f"""
      (SELECT COALESCE(array_to_json(array_agg(row_to_json(array_row))),'[]'::json) FROM (
      {template}
      ) array_row);
      """
      return sql


    connection_url = os.getenv("CONNECTION_URL")
    pool = ConnectionPool(connection_url)

    ```
3. In the [docker-compose.yml](../docker-compose.yml) file, the following environment variable was added to the backend service:
    ```yaml
    CONNECTION_URL: "${CONNECTION_LOCAL_DOCKER_URL}"
    ```

4. To use the module in 2. above, the [home_activities.py](../backend-flask/services/home_activities.py) service module imports the two objects, the *ConnectionPool* object and the *query_wrap_array* object.
    - The *query_wrap_array* is used to wrap the sql query
    - The *ConnectionPool* object *pool* is used to open a connection and fetch data from the database. The [home_activities.py](../backend-flask/services/home_activities.py) is shown below:
    ```python
    from datetime import datetime, timedelta, timezone
    from opentelemetry import trace

    tracer = trace.get_tracer("home-activities")
    from lib.db import pool, query_wrap_array

    class HomeActivities:
      def run(logger=None, cognito_user=None):
        # logger.info("Test from Home Activities")
        with tracer.start_as_current_span("home-activities-mock-data"):
          span = trace.get_current_span()
          now = datetime.now(timezone.utc).astimezone()
          span.set_attribute("app.now", now.isoformat())
          
          sql = query_wrap_array("""
          SELECT
            activities.uuid,
            users.display_name,
            users.handle,
            activities.message,
            activities.replies_count,
            activities.reposts_count,
            activities.likes_count,
            activities.reply_to_activity_uuid,
            activities.expires_at,
            activities.created_at
          FROM public.activities
          LEFT JOIN public.users ON users.uuid = activities.user_uuid
          ORDER BY activities.created_at DESC
          """)
          with pool.connection() as conn:
            with conn.cursor() as cur:
              cur.execute(sql)
              json = cur.fetchone()
          
          return json[0]
      ```
5. Running docker compose up and inspecting the frontend:
    ![db-frontennd](./images/db-frontend.png)

### **Create Lambda-Congito Trigger for Inserting Users into Database**
The goal of this chapter is to insert registered users post registration confirmation into the users table within cruddur database.
1. Firstly created a new function in the lambda service page. The following basic setup was used:
    - Author from scratch
    - Provide the function name
    - Runtime: Python3.8
    - Architecture: x86_64

2. In the new function page, I copied the following code into the editor and clicked deploy to save the code:
    ```python
    import os
    import json
    import psycopg2

    def lambda_handler(event, context):
        user = event['request']['userAttributes']
        user_display_name = user["name"]
        user_email = user["email"]
        user_handle = user["preferred_username"]
        user_cognito_id = user["sub"]
            
        try:
            conn = psycopg2.connect(os.getenv("CONNECTION_URL"))
            cur = conn.cursor()
            sql = f"""
            INSERT INTO public.users (
                display_name,
                email, 
                handle, 
                cognito_user_id
                ) 
            VALUES(
                %s, %s, %s, %s
                )
            """ 
            args= [
                user_display_name, 
                user_email, 
                user_handle, 
                user_cognito_id
                ]
                
            print(sql)
            cur.execute(sql, *args)
            conn.commit()
            print('Commit Done')

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            
        finally:
            if conn is not None:
                cur.close()
                conn.close()
                print('Database connection closed.')

        return event
    ```
3. To use the *psycopg2* we  needed to add a layer. There are several layer  arns available [here](https://github.com/jetbridge/psycopg2-lambda-layer) for use. However, I decided to build my own layer by doing the following:
    - Downloaded an awslambda-psycopg2 repo from [here](https://github.com/jkehler/awslambda-psycopg2.git)
    - Extracted out the psycopg2-3.8 directory and took note of its location
    - In the terminal: I did the following:
        ```bash
        mkdir -p python/lib/python3.8/site-packages/psycopg2

        cp <path-to-parent-directory>/psycopg2-3.8/* python/lib/python3.8/site-packages/psycopg2

        zip -r9 psycopg2-py38.zip python
        ````
    - In the lambda function page, I clicked on the burger button (top left) and selected layers located underneath *Additional resources*. I then selected *Create Layer*

    - Inputted all the necessary details and uploaded the zip file I created. Created the layer.
    - Back in my created function, while still in the code tab and scrolling to the bottom(Might change in the future because of Amazon's constant changes), I added the just created layer as a *custom layer*. 

4. The *CONNECTION_URL* indicated in the code uploaded above can be set in the *Configuration* -> *Environment Variable* tab. The url is the same as the *PROD_CONNECTION_URL* from earlier
    
5. To ensure that the lambda can make network calls, and additional policy was added to the lambda role by:   
    - In the  *Configuration* -> *Permissions* tab, I added an addition policy to the execution role. This was done by clicking on the Role name, which then redirects on to IAM Management console for the current lambda role. In there, the following steps were performed: Attach policies(from the Add permission dropdown) -> Create Police -> Choose a Service (Selected EC2) -> Switch editor to JSON (Click on JSON). Copied the following in it:
      ```json
      {
          "Version": "2012-10-17",
          "Statement": [
              {
                  "Effect": "Allow",
                  "Action": [
                      "ec2:CreateNetworkInterface",
                      "ec2:DeleteNetworkInterface",
                      "ec2:DescribeNetworkInterfaces",
                      "ec2:AttachNetworkInterface",
                      "ec2:DescribeInstances"
                  ],
                  "Resource": "*"
              }
          ]
      }
      ````
    - Reviewed Policy and created Policy. I then attached the created policy to the Lambda role
    - Inspected that the policy has been added by reviewing the policies available in the lambda function *Configuration* -> *Permissions* tab and in the *Resource summary* dropdown.

6. Headed over to cognito-> user pools -> < my-user-pool > -> User pool properties. In there, I added a lambda trigger with the following configuration:
  - Trigger Type: Sign-Up
  - Sign-Up: Post confirmation Trigger
  - Assign Lambda function: Lambda function just created

- Fired up the containers, navigated to new user sign-up and completed the process. Inspecting the cloudwatch logs and the rds user table, it shows it was successful.

    ![post-confirm-db](./images/post-confirm-db.png)



