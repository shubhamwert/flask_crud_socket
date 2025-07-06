from flask import jsonify, request
from flask_restx import Namespace, Resource, fields
from pydantic import ValidationError

from src.dbHandler.db import db
from src.models.models import Issue, IssuePermission, User
from src.notification.notification import socketio
from src.schema.schema import IssueCreate, IssuePut, IssueRead

IssuesApiNs = Namespace("issues", description="Issue operations")

# 🔧 Flask-RESTX model for SwaggerIssuePut docs
issue_model = IssuesApiNs.model(
    "Issue",
    {
        "title": fields.String(required=True, description="Title of the issue"),
        "description": fields.String(required=True, description="Markdown description"),
        "file_url": fields.String(required=False, description="Optional file URL"),
        "severity": fields.String(enum=["P0", "P1", "P2", "P3"], required=True),
        "status": fields.String(
            enum=["Open", "triaged", "in_progress", "done"], default="Open"
        ),
        "reported_by": fields.Integer(),
    },
)
issue_put_model = IssuesApiNs.model(
    "Issue",
    {
        "status": fields.String(
            enum=["Open", "triaged", "in_progress", "done"],
            required=True,
            default="Open",
        ),
    },
)
issue_response_model = IssuesApiNs.inherit(
    "IssueResponse", issue_model, {"id": fields.Integer()}
)


# 📬 POST /issues
@IssuesApiNs.route("")
class IssueList(Resource):
    @IssuesApiNs.marshal_list_with(issue_response_model)
    @IssuesApiNs.doc(
        params={
            "X-User-ID": {
                "description": "User ID",
                "in": "header",
                "type": "string",
                "required": True,
            }
        }
    )
    def get(self):
        """List all issues"""
        user_id = request.headers.get("X-User-ID", None)
        if user_id is None:
            return {"msg": "Unauthorized"}, 401

        if has_read_permission(user_id, None, "read"):
            issues = Issue.query.all()
            return [IssueRead.model_validate(i).model_dump() for i in issues]
        else:
            return {"msg": "Unauthorized"}, 401

    @IssuesApiNs.expect(issue_model)
    @IssuesApiNs.marshal_with(issue_response_model, code=201)
    def post(self):
        """Create a new issue"""
        try:
            payload = IssueCreate.model_validate(request.json)
            reporter_id = request.json.get("reported_by")
            reporter = User.query.get(reporter_id)
            print("here")
            if not reporter:
                return jsonify({"error": "Invalid reporter_id"}), 400

            issue = Issue(
                title=payload.title,
                description=payload.description,
                file_url=payload.file_url,
                severity=payload.severity,
                status=payload.status,
                reported_by=reporter_id,
            )

            db.session.add(issue)
            db.session.commit()
            iss = IssueRead.model_validate(issue)
            perm = IssuePermission(
                issue_id=iss.id,
                user_id=reporter_id,
                role="reporter",  # or "write"
            )
            db.session.add(perm)
            db.session.commit()
            permitted_users = IssuePermission.query.filter_by(issue_id=issue.id).all()
            for users in permitted_users:
                socketio.emit(
                    "new_issue",
                    IssueRead.model_validate(issue).model_dump(),
                    room=f"user_{users.user_id}",
                )

            return IssueRead.model_validate(issue).model_dump(), 201
        except ValidationError as e:
            print("err", e)
            return {"errors": e.errors()}, 400


@IssuesApiNs.route("/<int:id>")
@IssuesApiNs.doc(
    params={
        "X-User-ID": {
            "description": "User ID",
            "in": "header",
            "type": "string",
            "required": True,
        }
    }
)
@IssuesApiNs.param("id", "Issue identifier")
class IssueResource(Resource):
    @IssuesApiNs.marshal_with(issue_response_model)
    def get(self, id):
        """Get issue by ID"""
        user_id = request.headers.get("X-User-ID", None)
        if user_id is None:
            return {"errors": "Not Authorized"}, 401

        if has_read_permission(user_id, id, "read"):
            issue = Issue.query.get_or_404(id)
            return IssueRead.model_validate(issue).model_dump()
        else:
            return {"errors": "Not Authorized"}, 401

    @IssuesApiNs.expect(issue_put_model)
    @IssuesApiNs.doc(
        params={
            "X-User-ID": {
                "description": "User ID",
                "in": "header",
                "type": "string",
                "required": True,
            }
        }
    )
    @IssuesApiNs.marshal_with(issue_response_model)
    def put(self, id):
        """Update issue by ID"""
        user_id = request.headers.get("X-User-ID", None)
        if not user_id:
            return {"msg": "Unauthorised"}, 401
        issue = Issue.query.get_or_404(id)
        if has_edit_permissions(user_id=user_id, issue_id=id):
            try:
                payload = IssuePut.model_validate(request.json)
                issue.status = payload.status
                db.session.commit()
                permitted_users = IssuePermission.query.filter_by(
                    issue_id=issue.id
                ).all()
                print(permitted_users)
                for users in permitted_users:
                    socketio.emit(
                        "new_issue",
                        IssueRead.model_validate(issue).model_dump(),
                        room=f"user_{users.user_id}",
                    )

                return IssueRead.model_validate(issue).model_dump()
            except ValidationError as e:
                print(e)
                return {"errors": e.errors()}, 500

    def delete(self, id):
        """Delete issue by ID"""
        return {"message": "Forbidden"}, 405
        issue = Issue.query.get_or_404(id)
        db.session.delete(issue)
        db.session.commit()
        return {"message": f"Issue {id} deleted"}, 204


def has_read_permission(user_id, issue_id, action="read"):
    user = User.query.get(user_id)
    if not user:
        return False

    if user.role == "admin":
        return True
    if issue_id is None:
        return False
    perm = IssuePermission.query.filter_by(issue_id=issue_id, user_id=user_id).first()
    if not perm:
        return False

    if perm.role:
        return True
    return False


def has_edit_permissions(
    user_id,
    issue_id,
):
    user = User.query.get(user_id)
    if not user:
        return False

    if user.role == "admin":
        return True
    if issue_id is None:
        return False
    perm = IssuePermission.query.filter_by(issue_id=issue_id, user_id=user_id).first()
    if not perm:
        return False
    if perm.role == "manager":
        return True
    return False
