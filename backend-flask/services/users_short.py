from lib.db import db

class UsersShort:
  def run(handle):
    sql = db.read_sql_template('users','short')
    results = db.query_object_json(sql, **{
      'handle': handle
    })
    return results