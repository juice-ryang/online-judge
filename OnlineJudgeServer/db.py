from datetime import datetime
from enum import Enum
from json import dumps

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy_utils import ChoiceType as EnumType

db = SQLAlchemy()
admin = Admin()


class JudgeStatus(Enum):
    PENDING = 0
    STARTED = 1
    FAILED = 2
    FINISHED = 3


class JudgeFeedback(db.Model):
    __tablename__ = "feedback"

    filename = db.Column(db.String(36), primary_key=True)  # TODO: UUID
    filedata = db.Column(db.LargeBinary(), nullable=True)
    cur_idx = db.Column(db.Integer, default=0)
    max_idx = db.Column(db.Integer, nullable=False)
    status = db.Column(
            EnumType(
                JudgeStatus,
                impl=db.Integer(),
            ),
            default=JudgeStatus['PENDING'],
    )
    cur_json_idx = db.Column(db.Integer, default=0)
    expected_output = db.Column(db.String(1024), nullable=True)
    actual_output = db.Column(db.String(1024), nullable=True)
    created = db.Column(db.DateTime, default=datetime.now)
    updated = db.Column(db.String(30), nullable=False)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        super().__setattr__('updated', str(datetime.now()))

    def __str__(self):
        output = {}
        for key in self.__dict__:
            if key[0] == '_':
                pass
            elif key in ('filedata'):
                pass
            elif key in ('created', 'status'):
                output[key] = str(getattr(self, key))
            elif key in ('expected_output', 'actual_output'):
                value = getattr(self, key)
                if value is not None:
                    output[key] = value  # XXX: JudgeFeedback._Brrrrify(value)
            else:
                value = getattr(self, key)
                if value is not None:
                    output[key] = value
        return dumps(output, sort_keys=True, indent=2)

    @staticmethod
    def _Brrrrify(inputs, before='\n', after='<br>', ignores=('\r',)):
        """please god save us."""
        inputs = list(inputs)
        while inputs.count(before):
            inputs[inputs.index(before)] = after
        for ign in ignores:
            while inputs.count(ign):
                inputs.remove(ign)
        return ''.join(inputs)


def monkeypatch_db_celery(app, celery):
    """Let Celery can change the content of DB with App context."""
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask


admin.add_view(ModelView(JudgeFeedback, db.session))

