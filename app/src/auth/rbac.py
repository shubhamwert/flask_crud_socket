# pylint: disable=too-few-public-methods
from flask import request
from flask_restx import Namespace, Resource, fields
from pydantic import ValidationError

from src.models.models import IssuePermission, db
from src.schema.schema import IssuePermissionCreate, IssuePermissionRead

ns_perm = Namespace("permissions", description="Manage issue permissions")

# Swagger model
permission_model = ns_perm.model(
    "IssuePermission",
    {
        "user_id": fields.Integer(required=True),
        "issue_id": fields.Integer(required=True),
        "role": fields.String(enum=["read", "write", "admin"], required=True),
    },
)

permission_response = ns_perm.inherit(
    "PermissionResponse", permission_model, {"id": fields.Integer()}
)


@ns_perm.route("")
class PermissionList(Resource):
    @ns_perm.marshal_list_with(permission_response)
    def get(self):
        """List all issue permissions"""
        perms = IssuePermission.query.all()
        return [IssuePermissionRead.model_validate(p).model_dump() for p in perms]

    @ns_perm.expect(permission_model)
    @ns_perm.marshal_with(permission_response, code=201)
    def post(self):
        """Grant access to an issue"""
        try:
            payload = IssuePermissionCreate.model_validate(request.json)
            perm = IssuePermission(**payload.model_dump())
            db.session.add(perm)
            db.session.commit()
            return IssuePermissionRead.model_validate(perm).model_dump(), 201
        except ValidationError as e:
            return {"errors": e.errors()}, 400


@ns_perm.route("/<int:id>")
@ns_perm.param("id", "Permission ID")
class PermissionResource(Resource):
    @ns_perm.expect(permission_model)
    @ns_perm.marshal_with(permission_response)
    def put(self, id):
        """Update a permission (change role)"""
        perm = IssuePermission.query.get_or_404(id)
        try:
            payload = IssuePermissionCreate.model_validate(request.json)
            for key, value in payload.model_dump().items():
                setattr(perm, key, value)
            db.session.commit()
            return IssuePermissionRead.model_validate(perm).model_dump()
        except ValidationError as e:
            return {"errors": e.errors()}, 400

    def delete(self, id):
        """Revoke issue access"""
        perm = IssuePermission.query.get_or_404(id)
        db.session.delete(perm)
        db.session.commit()
        return {"message": "Permission deleted"}, 204
