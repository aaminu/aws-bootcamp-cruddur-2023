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
        args = [
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
