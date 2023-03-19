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
