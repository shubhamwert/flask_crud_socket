# app/routes/user_routes.py
from flask import request
from flask_restx import Namespace, Resource
from pydantic import ValidationError

from src.dbHandler.db import db
from src.models.models import User
from src.schema.schema import UserCreate, UserLogin, UserRead

AuthApiNs = Namespace("users", description="User operations")


@AuthApiNs.route("/register")
class UserRegister(Resource):
    def post(self):
        try:
            data = UserCreate(**request.get_json())
        except ValidationError as e:
            return {"errors": e.errors()}, 400

        if User.query.filter_by(username=data.username).first():
            return {"message": "Username already exists."}, 409

        user = User(username=data.username)
        user.set_password(data.password)
        user.role = "read"
        db.session.add(user)
        db.session.commit()

        return {"message": "User registered successfully."}, 201


@AuthApiNs.route("/login")
class UserLoginRoute(Resource):
    def post(self):
        try:
            data = UserLogin(**request.get_json())
        except ValidationError as e:
            return {"errors": e.errors()}, 400

        user = User.query.filter_by(username=data.username).first()
        print(user)
        if user and user.check_password(data.password):
            user = UserRead.model_validate(user)
            print("################", user)
            return {
                "message": "Login successful.",
                "metdata": user.model_dump(mode="json"),
            }, 200

        return {"message": "Invalid username or password."}, 401
