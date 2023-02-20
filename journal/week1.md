# Week 1 — App Containerization

## Required Homework
1. Containerization or both frontend and back end was completed by 
    -   Writing a dockerfile for the frontend located [here](../frontend-react-js/Dockerfile)
    - Writing a dockerfile for the backend located [here](../backend-flask/Dockerfile)
    - Writing a docker-compe file located here  [here](../docker-compose.yml)

2. Documented the notifications endpoint for the openAPI, wrote the flask backend and react front  for notifications. Afterwards ``` docker compose up ``` was run in the terminal to start the required containers. Please refer to the images below with modified notifications as proof of work

    Notifications Backend Response:

    ![Notif](./images/notif2.png)

    Notifications Page:

    ![Notif](./images/notif1.png)

3. Updated the docker-compose file and gitpod yaml file per instruction and ran a DynamoDB local container Please see images below;

    Creating a Table in DynamoDB:

    ![dyna_crea](./images/dyn_cre.png)

    Inserting an Item in the Table from Above:

    ![dyna_put](./images/dyn_put.png)

4. Also updated the gitpod yaml file along side 3. above. Please see image below as proof of workings

    Postgres DB:

    ![postgres](./images/postgre.png)

5. Added an additional task to the gitpod yaml file that installs the required node modules into the /frontend-react-js folder during start-up. Without this option, my app failed after I started a new workspace and manually forgot to install it. The addition task can be seen below:
    ```yaml
    // this belongs to the task
        - name: npm-init
            init: |
                cd /workspace/aws-bootcamp-cruddur-2023/frontend-react-js
                npm i
    ```