import os
from tempfile import TemporaryDirectory
import uuid
from json import load

from celery import (
    Celery,
    chain,
)
from chardet import detect as Chardet
from flask import (
    Flask,
    url_for,
    render_template,
    redirect,
    request,
    send_from_directory,
)
from flaskext.markdown import Markdown
from sqlalchemy_utils import (
    create_database,
    database_exists,
)
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import AnyConverter

from . import problems
from .db import (
    admin,
    db,
    monkeypatch_db_celery,
    JudgeStatus as Status,
    JudgeFeedback as Feedback,
)
from .process_capsule import DEFAULT_PYTHON
from .terminal_capsule import Validate

app = Flask(__name__)
app.debug = True
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['CELERY_ACCEPT_CONTENT'] = ['json']
app.config['CELERY_TASK_SERIALIZER'] = 'json'
app.config['CELERY_RESULT_SERIALIZER'] = 'json'
app.config['CELERY_TIMEZONE'] = 'Asia/Seoul'
app.config['CELERY_BROKER_URL'] = 'amqp://'
app.config['CELERY_RESULT_BACKEND'] = 'amqp'
app.config['VIRTUAL_ENV'] = DEFAULT_PYTHON
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://db:db@db/db?charset=utf8mb4'

celery = Celery(app.name)
celery.conf.update(app.config)

admin.init_app(app)
db.app = app
db.init_app(app)
monkeypatch_db_celery(app, celery)

Markdown(app)


@app.before_first_request
def init_db():
    #if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
    #    create_database(app.config['SQLALCHEMY_DATABASE_URI'])
    db.drop_all()
    db.create_all()


def task_judge(problemset, problem, filename, data):
    PROBLEMS = problems.get_testcase_for_judging(problemset, problem)
    subtasks = chain(
        [subtask_judge.s(
            filename=filename,
            idx=idx,
            json=tc['json']) for idx, tc in enumerate(PROBLEMS['testcases'])]
    )
    feedback = Feedback()
    feedback.filename = filename
    feedback.max_idx = PROBLEMS['N'] - 1
    feedback.filedata = data
    db.session.add(feedback)
    db.session.commit()
    return subtasks


# WHENEVER CHANGES HAPPENED FOR CELERY, NEED TO RESTART CELERY!
@celery.task(track_started=True, ignore_result=False)
def subtask_judge(previous_return=None, **kwargs):
    filename = kwargs['filename']
    found = Feedback.query.get(filename)

    if not previous_return:  # first run,
        found.status = Status['STARTED']
        found.cur_idx = 0
        db.session.commit()

    with TemporaryDirectory() as dir:
        filepath = os.path.join(dir, filename)
        with open(filepath, 'wb') as f:
            f.write(found.filedata)
        return subtask_judge_run(dir, **kwargs)


def subtask_judge_run(dir, **kwargs):
    filename = kwargs['filename']
    idx = kwargs['idx']
    json = kwargs['json']

    class JudgeFailed(Exception):
        pass

    reported_stdout = []

    def report(this):
        def _(*args, **kwargs):
            out = this(*args, **kwargs)
            func = this.__name__
            if func == "_START":
                found = Feedback.query.get(filename)
                found.cur_idx = idx
                db.session.commit()
            elif func == "_PASS":
                found = Feedback.query.get(filename)
                found.cur_json_idx += 1
                db.session.commit()
            elif func == "_FAIL":
                raise JudgeFailed()
            elif func == "_GOT_STDOUT":
                reported_stdout.append(out)
            return out
        return _

    try:
        Validate(
            this_program='./%s' % (filename,),
            from_json=json,
            report=report,
            cwd=dir,
        )
    except JudgeFailed as Failed:
        found = Feedback.query.get(filename)
        found.status = Status['FAILED']
        expected = ''
        with open(json) as fp:
            stdouts = [stdout for _, stdout in load(fp)]
            expected = ''.join(stdouts[:found.cur_json_idx + 1])
        found.expected_output = expected
        found.actual_output = ''.join(reported_stdout)
        db.session.commit()
        raise Failed
    else:
        found = Feedback.query.get(filename)
        if found.cur_idx == found.max_idx:
            found.status = Status['FINISHED']
            db.session.commit()
    return str(found)
# WHENEVER CHANGES HAPPENED FOR CELERY, NEED TO RESTART CELERY!


@app.route('/')
def index():
    return render_template(
            'index.html',
            problemsets=problems.get_all_sets(),
    ), 200


@app.route('/favicon.ico/')
def favicon():
    return redirect('/static/favicon.ico')


def problemset__url_rules(_):
    return AnyConverter(_, *problems.get_all_sets())


def problem__url_rules(_):
    rules = []
    for problemset, problem_names in problems.pdict.items():
        for problem in problem_names:
            rules.append('/'.join((problemset, problem)))
    return AnyConverter(_, *rules)


app.url_map.converters['problemset'] = lambda _: problemset__url_rules(_)
app.url_map.converters['problem'] = lambda _: problem__url_rules(_)


@app.route('/<problemset:problemset>/')
def problemset(problemset):
    return render_template(
            'problemset.html',
            problemset=problemset,
            problems=problems.get_problems(problemset),
    ), 200


@app.route('/<problem:problem>/', methods=['GET', 'POST'])
def problem(problem):
    problemset, problem = problem.split('/')
    if request.method == 'GET':
        # TODO: Oh God, ... Please refactor these.
        return render_template(
                'problem.html',
                problemset=problemset,
                problem=problem,
                descrpition=problems.get_problem_description(
                    problemset, problem
                ),
                submit_url=url_for(
                    'problem_submit',
                    problem='/'.join((problemset, problem)),
                ),
        ), 200
    else:
        return redirect(url_for('submit'), code=307)


@app.route('/<problem:problem>/<filename>', methods=['GET'])
def additional_file_serve(problem, filename):
    problemset, problem = problem.split('/')
    # TODO: SECURITY WARNING!!!!!
    is_accepted = False
    for ext in [
        '.png',
    ]:
        if filename.endswith(ext):
            is_accepted = True
            break
    if not is_accepted:
        return redirect(
                url_for('problem', problem='/'.join((problemset, problem)))
        )
    path = os.path.join("problems/", problemset, problem)
    return send_from_directory(path, filename)


@app.route('/<problem:problem>/submit/', methods=['GET', 'POST'])
def problem_submit(problem):
    problemset, problem = problem.split('/')
    if request.method == 'GET':
        return redirect(
                url_for('problem', problem='/'.join((problemset, problem)))
        )
    else:
        filename, data = submit()
        task_judge(problemset, problem, filename, data).apply_async(countdown=1.5)
        return render_template(
                'result.html',
                filename=filename,
                problemset=problemset,
                problem=problem,
        )


@app.route('/api/status/<filename>', methods=['GET'])
def status(filename):
    found = Feedback.query.get(filename)
    if not found:
        return 'Not Found', 404
    last_updated = request.args.get('last_updated')
    if last_updated == str(found.updated):
        return 'not updated yet', 304
    return str(found)


def submit():
    f = request.files['upfile']
    filename = str(uuid.uuid4())
    with TemporaryDirectory() as dir:
        filepath = os.path.join(dir, filename)
        f.save(filepath + '.origin')
        data = None
        with open(filepath + '.origin', 'rb') as f_origin:
            data = f_origin.read()
        det = Chardet(data)
        data2 = None
        if 'encoding' in det:
            data2 = data.decode(det['encoding']).encode('utf-8')
            with open(filepath, 'wb') as f_real:
                f_real.write(data2)
        return filename, data2
