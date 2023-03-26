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

    def read_sql_template(self, *args, log=False):
        """ Reading SQL Templates in db Directory"""
        path_list = list((app.root_path, 'db', 'sql',) + args)
        path_list[-1] = path_list[-1] + ".sql"

        template_path = os.path.join(*path_list)

        green = '\033[92m'
        no_color = '\033[0m'
        if log:
            app.logger.info("\n")
            app.logger.info(
                f'{green} Load SQL Template: {template_path} {no_color}')

        with open(template_path, 'r') as f:
            template_content = f.read()
        return template_content

    def print_params(self, log=False, **params):
        """Print Parameters passed into SQL"""
        blue = '\033[94m'
        no_color = '\033[0m'
        if log:
            app.logger.info(f'{blue} SQL Params:{no_color}')
            for key, value in params.items():
                app.logger.info(f"{key}: {value}")

    def print_sql(self, title, sql, log=False):
        """Print SQL Statement"""
        cyan = '\033[96m'
        no_color = '\033[0m'
        if log:
            app.logger.info(f'{cyan} SQL STATEMENT-[{title}]------{no_color}')
            app.logger.info(sql)

    def query_commit(self, sql, log=False, **params):
        """ Commit a Query"""
        pattern = r"\bRETURNING\b"
        is_returning_id = re.search(pattern, sql)

        if is_returning_id is not None:
            self.print_sql('commit with returning', sql, log)
        else:
            self.print_sql('commit without return', sql, log)

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
            self.print_sql_err(err, log)

    def query_array_json(self, sql, log=False, **params):
        """Query Database and return an array of json"""
        self.print_sql('array', sql, log)
        self.print_params(log, **params)

        wrapped_sql = self.query_wrap_array(sql)
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(wrapped_sql, params)
                json = cur.fetchone()
                return json[0]

    def query_object_json(self, sql, log=False, **params):
        """Query Database and return an array of json"""
        self.print_sql('json', sql, log)
        self.print_params(log, **params)

        wrapped_sql = self.query_wrap_object(sql)
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(wrapped_sql, params)
                json = cur.fetchone()
                if json == None:
                    return {}
                else:
                    return json[0]

    def query_value(self,sql, log=False, **params):
        self.print_sql('value',sql,log)
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql,params)
                json = cur.fetchone()
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

    def print_sql_err(self, err, log=False):
        # get details about the exception
        err_type, err_obj, traceback = sys.exc_info()

        # get the line number when exception occured
        line_num = traceback.tb_lineno

        if log:
            # print the connect() error
            app.logger.info("\npsycopg ERROR:", err, "on line number:", line_num)
            app.logger.info("psycopg traceback:", traceback, "-- type:", err_type)

            # print the pgcode and pgerror exceptions
            app.logger.info("pgerror:", err.pgerror)
            app.logger.info("pgcode:", err.pgcode, "\n")


db = Db()
