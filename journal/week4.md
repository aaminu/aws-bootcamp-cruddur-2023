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
            args= (
                user_display_name, 
                user_email, 
                user_handle, 
                user_cognito_id
            )
                
            print(sql)
            cur.execute(sql, args)
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


### **Creating New Activities with a Database Insert**
1. Refactored the [db.py](../backend-flask/lib/db.py) module to provide extra functionality. PS: Mine is a bit different from Andrew's incase you are reading mine. Pay attention to my use of *parms(positional arguments) and **parrams(named arguments)
    ```python
    import os
    import re
    import sys
    from flask import current_app as app
    from psycopg_pool import ConnectionPool


    class Db:
        def __init__(self):
            self.init_pool()

        def init_pool(self):
            """Start a Connection Pool"""
            connection_url = os.getenv("CONNECTION_URL")
            self.pool = ConnectionPool(connection_url)

        def read_sql_template(self, *args):
            """ Reading SQL Templates in db Directory"""
            path_list = list((app.root_path, 'db', 'sql',) + args)
            path_list[-1] = path_list[-1] + ".sql"

            template_path = os.path.join(*path_list)

            green = '\033[92m'
            no_color = '\033[0m'
            app.logger.info("\n")
            app.logger.info(
                f'{green} Load SQL Template: {template_path} {no_color}')

            with open(template_path, 'r') as f:
                template_content = f.read()
            return template_content

        def print_params(self, **params):
            """Print Parameters passed into SQL"""
            blue = '\033[94m'
            no_color = '\033[0m'
            app.logger.info(f'{blue} SQL Params:{no_color}')
            for key, value in params.items():
                app.logger.info(f"{key}: {value}")

        def print_sql(self, title, sql):
            """Print SQL Statement"""
            cyan = '\033[96m'
            no_color = '\033[0m'
            app.logger.info(f'{cyan} SQL STATEMENT-[{title}]------{no_color}')
            app.logger.info(sql)

        def query_commit(self, sql, **params):
            """ Commit a Query"""
            pattern = r"\bRETURNING\b"
            is_returning_id = re.search(pattern, sql)

            if is_returning_id is not None:
                self.print_sql('commit with returning', sql)
            else:
                self.print_sql('commit without return', sql)

            try:
                with self.pool.connection() as conn:
                    cur = conn.cursor()
                    cur.execute(sql, params)
                    if is_returning_id:
                        returning_id = cur.fetchone()[0]
                    conn.commit()
                    if is_returning_id:
                        return returning_id
            except Exception as err:
                self.print_sql_err(err)

        def query_array_json(self, sql, **params):
            """Query Database and return an array of json"""
            self.print_sql('array', sql)
            self.print_params(**params)

            wrapped_sql = self.query_wrap_array(sql)
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(wrapped_sql, params)
                    json = cur.fetchone()
                    app.logger.info(f"Returned JSON: {json}")
                    return json[0]

        def query_object_json(self, sql, **params):
            """Query Database and return an array of json"""
            self.print_sql('json', sql)
            self.print_params(**params)

            wrapped_sql = self.query_wrap_object(sql)
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(wrapped_sql, params)
                    json = cur.fetchone()
                    if json == None:
                        return {}
                    else:
                        return json[0]

        def query_wrap_object(self, template):
            """Wrap query for a json object return"""
            sql = f"""
                    (SELECT COALESCE(row_to_json(object_row),'{{}}'::json) FROM (
                    {template}
                    ) object_row);
                """
            return sql

        def query_wrap_array(self, template):
            """Wrap query for an array of json object return"""
            sql = f"""
                    (SELECT COALESCE(array_to_json(array_agg(row_to_json(array_row))),'[]'::json) FROM (
                    {template}
                    ) array_row);
                """
            return sql

        def print_sql_err(self, err):
            # get details about the exception
            err_type, err_obj, traceback = sys.exc_info()

            # get the line number when exception occured
            line_num = traceback.tb_lineno

            # print the connect() error
            app.logger.info("\npsycopg ERROR:", err, "on line number:", line_num)
            app.logger.info("psycopg traceback:", traceback, "-- type:", err_type)

            # print the pgcode and pgerror exceptions
            app.logger.info("pgerror:", err.pgerror)
            app.logger.info("pgcode:", err.pgcode, "\n")


    db = Db()
    ```
2. Refactored the [home_activities.py](../backend-flask/services/home_activities.py) to make use of the db object from above:
    ```python
    from lib.db import db
    from datetime import datetime, timedelta, timezone
    from opentelemetry import trace

    tracer = trace.get_tracer("home-activities")


    class HomeActivities:
        def run(logger=None, cognito_user=None):
            # logger.info("Test from Home Activities")
            with tracer.start_as_current_span("home-activities-mock-data"):
                span = trace.get_current_span()
                now = datetime.now(timezone.utc).astimezone()
                span.set_attribute("app.now", now.isoformat())

                sql = db.read_sql_template('activities', 'home')
                results = db.query_array_json(sql)

                return results
    ```
3. Refactored the [create_activity.py](../backend-flask/services/create_activity.py) to make use of the db object from above:
    ```python
    from datetime import datetime, timedelta, timezone
    from lib.db import db


    class CreateActivity:
        def run(message, user_handle, ttl):
            model = {
                'errors': None,
                'data': None
            }

            now = datetime.now(timezone.utc).astimezone()

            if (ttl == '30-days'):
                ttl_offset = timedelta(days=30)
            elif (ttl == '7-days'):
                ttl_offset = timedelta(days=7)
            elif (ttl == '3-days'):
                ttl_offset = timedelta(days=3)
            elif (ttl == '1-day'):
                ttl_offset = timedelta(days=1)
            elif (ttl == '12-hours'):
                ttl_offset = timedelta(hours=12)
            elif (ttl == '3-hours'):
                ttl_offset = timedelta(hours=3)
            elif (ttl == '1-hour'):
                ttl_offset = timedelta(hours=1)
            else:
                model['errors'] = ['ttl_blank']

            if user_handle == None or len(user_handle) < 1:
                model['errors'] = ['user_handle_blank']

            if message == None or len(message) < 1:
                model['errors'] = ['message_blank']
            elif len(message) > 280:
                model['errors'] = ['message_exceed_max_chars']

            if model['errors']:
                model['data'] = {
                    'handle':  user_handle,
                    'message': message
                }
            else:
                expires_at = (now + ttl_offset)
                uuid = CreateActivity.create_activity(
                    user_handle, message, expires_at)

                object_json = CreateActivity.query_object_activity(uuid)
                model['data'] = object_json
            return model

        def create_activity(handle, message, expires_at):
            sql = db.read_sql_template('activities', 'create')
            uuid = db.query_commit(sql,
                                handle=handle,
                                message=message,
                                expires_at=expires_at
                                )
            return uuid

        def query_object_activity(uuid):
            sql = db.read_sql_template('activities', 'object')
            return db.query_object_json(sql, uuid=uuid
                                        )
    ```
4. Moved SQL statements from python modules and created sql files in [/backend-flask/db/sql/activities](../backend-flask/db/sql/) directory.

5. To get the posting of an activity to work, I had to change the hardcoded "andrewbrown" to the username passed from the front end. This fix and can be done by: 
    
    - In the [HomeFeedPage.js](../frontend-react-js/src/pages/HomeFeedPage.js), forward the user data to the ActivityForm by:
        ```js
        return (
        <article>
        <DesktopNavigation user={user} active={'home'} setPopped={setPopped} />
        <div className='content'>
            <ActivityForm
            user_handle={user} //Pass the user object here
            popped={popped}
            setPopped={setPopped}
            setActivities={setActivities}
            />
            <ReplyForm
            activity={replyActivity}
            popped={poppedReply}
            setPopped={setPoppedReply}
            setActivities={setActivities}
            activities={activities}
            />
            <ActivityFeed
            title="Home"
            setReplyActivity={setReplyActivity}
            setPopped={setPoppedReply}
            activities={activities}
            />
        </div>
        <DesktopSidebar user={user} />
        </article>
        );
        ```
    - In the [ActivityForm.js](../frontend-react-js/src/components/ActivityForm.js), include the user handle in the post request message:
        ```js
        const onsubmit = async (event) => {
        event.preventDefault();
        try {
        const backend_url = `${process.env.REACT_APP_BACKEND_URL}/api/activities`
        console.log('onsubmit payload', message)
        const res = await fetch(backend_url, {
            method: "POST",
            headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
            },
            body: JSON.stringify({
            user_handle: props.user_handle.handle, //include it the post request
            message: message,
            ttl: ttl
            }),
        });
        let data = await res.json();
        if (res.status === 200) {
            // add activity to the feed
            props.setActivities(current => [data, ...current]);
            // reset and close the form
            setCount(0)
            setMessage('')
            setTtl('7-days')
            props.setPopped(false)
        } else {
            console.log(res)
        }
        } catch (err) {
            console.log(err);
        }
        }
        ```
    - Finally in the [app.py](../backend-flask/app.py) file, grab the user_handle:

        ```python
        @app.route("/api/activities", methods=['POST', 'OPTIONS'])
        @cross_origin()
        def data_activities():
            user_handle = request.json['user_handle']
            message = request.json['message']
            ttl = request.json['ttl']
            model = CreateActivity.run(message, user_handle, ttl)
            if model['errors'] is not None:
                return model['errors'], 422
            else:
                return model['data'], 200
            return
        ```
6. See below for successfully posted crudds:

    ![crudds](./images/Crudds.png)