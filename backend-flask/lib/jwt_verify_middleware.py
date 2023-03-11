from flask import request


class JWTVerificationMiddleware():
    '''
    Simple JWT verification middleware for a flask app.
    '''

    def __init__(self, app, decoder_verifier_handler):
        """
        Input:
            app:                           Flask app.wsgi_app handle
            decoder_verifier_handler:      JWT decoder and verifier
                                            This object should have a method called verify() which
                                            takes an argument/variable called <token>
        """
        self.app = app
        self.app.logger.info("initializing jwt decoder middleware")
        self.token_claimer = decoder_verifier_handler

    def _before_request(self):
        headers = request.headers
        access_token = self.token_claimer.extract_access_token(request.headers)
        
        self.app.logger.info(request.__dict__)
        return self.app.wsgi_app(environ, start_response)
