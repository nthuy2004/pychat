from flask import Flask, make_response, request, Response
from config import Config

from flask_cors import CORS, cross_origin

from routes.api import reg_bp as api_bp


def create_app(config=Config):
    app = Flask(__name__)
    cors = CORS(app)
    app.config.from_object(config)
    reg_ext(app)
    reg_bp(app)
    return app


def reg_ext(app):
    from extensions import db, bcrypt, redis_client
    db.init_app(app)
    bcrypt.init_app(app)
    redis_client.init_app(app)

    print(redis_client.set("hello"," [1, 2, 3]"))
    print(redis_client.get("hello"))


def reg_bp(app):
    api_bp(app)


if __name__ == '__main__':
    app = create_app()

    @app.after_request
    def add_header(response):
        if request.method.lower() == 'options':
            return Response()
        return response
    app.run(debug=True)
