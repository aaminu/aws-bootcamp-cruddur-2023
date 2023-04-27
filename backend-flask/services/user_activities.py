from lib.db import db
from opentelemetry import trace

tracer = trace.get_tracer("user-activities")

class UserActivities:
  def run(user_handle):
    with tracer.start_as_current_span("user-data"):
      span = trace.get_current_span()
      model = {
        'errors': None,
        'data': None
      }

      if user_handle == None or len(user_handle) < 1:
        model['errors'] = ['blank_user_handle']
      else:
        print("else:")
        sql = db.template('users','show')
        results = db.query_object_json(sql, handle=user_handle)
        model['data'] = results

      return model