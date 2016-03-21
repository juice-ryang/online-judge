from enum import Enum

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy_utils import ChoiceType as EnumType

db = SQLAlchemy()


class JudgeStatus(Enum):
    """."""
    PENDING = 0
    STARTED = 1
    SUCCESS = 2
    FAILED = 3


class JudgeFeedback(db.Model):
    """."""
    __tablename__ = "feedback"

    filename = db.Column(db.String(50), primary_key=True)
    idx = db.Column(db.Integer, primary_key=True)
    status = db.Column(EnumType(JudgeStatus), default=JudgeStatus.PENDING)
    expected_output = db.Column(db.String(1024), nullable=True)
    actual_output = db.Column(db.String(1024), nullable=True)


def monkeypatch_db_celery(app, celery):
    """Let Celery can change the content of DB with App context."""
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
