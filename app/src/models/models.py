from src.dbHandler.db import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    role = db.Column(db.String(8), nullable=True)
    def __repr__(self):
        return f"<User id={self.id} username={self.username} role={self.role}>"
class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)  # markdown
    file_url = db.Column(db.String(512), nullable=True)
    severity = db.Column(db.String(10), nullable=False)  # Enum: P0-P3
    status = db.Column(db.String(20), nullable=False, default="Open")
    permissions = db.relationship('IssuePermission', back_populates='issue', cascade='all, delete-orphan')
    reported_by = db.Column(db.Integer,nullable=False)
class IssuePermission(db.Model):
    __tablename__ = 'issue_permission'

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="read")  # Possible values: "read", "write", "admin"

    issue = db.relationship('Issue', back_populates='permissions')
    user = db.relationship('User')