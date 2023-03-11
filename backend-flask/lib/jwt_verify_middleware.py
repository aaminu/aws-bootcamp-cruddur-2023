from werkzeug.wrappers import Request, Response, ResponseStream


class JWTVerificationMiddleware():
    '''
    Simple JWT verification middleware for a flask app.
    '''

    def __init__(self, app, decoder_verifier_handler):
        """
        Input:
            app:                           Flask app handle
            decoder_verifier_handler:      JWT decoder and verifier
                                            This object should have a method called verify() which
                                            takes an argument/variable called <token>
        """
        self.app = app.wsgi_app
        self.token_claimer = decoder_verifier_handler
        self.logger = app.logger

    def __call__(self, environ, start_response):
        request = Request(environ)
        self.logger.debug(request)
