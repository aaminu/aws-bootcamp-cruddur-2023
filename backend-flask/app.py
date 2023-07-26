from flask import Flask
from flask import request, g

from lib.rollbar import init_rollbar
from lib.xray import init_xray
from lib.cors import init_cors
from lib.cloudwatch import init_cloudwatch
from lib.honeycomb import init_honeycomb
from lib.jwt_verify_middleware import JWTVerificationMiddleware, jwt_decoder

import routes.general
import routes.activities
import routes.users
import routes.messages


app = Flask(__name__)

# Init
init_xray(app)
init_honeycomb(app)
init_cors(app)
JWTVerificationMiddleware(app, jwt_decoder) # Wrap app with middleware
with app.app_context():
    g.rollbar = init_rollbar(app)


# Routes
routes.general.load(app)
routes.activities.load(app)
routes.users.load(app)
routes.messages.load(app)

if __name__ == "__main__":
    app.run(debug=True)
