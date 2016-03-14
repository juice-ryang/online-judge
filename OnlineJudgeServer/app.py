import os
import time
import uuid

from celery import (
    Celery,
    chain,
)
from flask import (
    Flask,
    url_for,
    render_template,
    redirect,
    request,
    jsonify,
    current_app,
)
from flaskext.markdown import Markdown

import problems
from process_capsule import DEFAULT_PYTHON
from terminal_capsule import Validate

app = Flask(__name__)
app.config['CELERY_ACCEPT_CONTENT'] = ['json']
app.config['CELERY_TASK_SERIALIZER'] = 'json'
app.config['CELERY_RESULT_SERIALIZER'] = 'json'
app.config['CELERY_TIMEZONE'] = 'Asia/Seoul'
app.config['CELERY_BROKER_URL'] = 'amqp://guest@localhost//'
app.config['CELERY_RESULT_BACKEND'] = app.config['CELERY_BROKER_URL']
app.config['VIRTUAL_ENV'] = DEFAULT_PYTHON

celery = Celery(app.name)
celery.conf.update(app.config)

Markdown(app)


def report(this):
    def _(*args, **kwargs):
        out = this(*args, **kwargs)
        func = this.__name__
        if func == "_FAIL":
            pass
        elif func == '_PASS':
            pass
        return out
    return _


# WHENEVER CHANGES HAPPENED FOR CELERY, NEED TO RESTART CELERY!
def task_judge(problemset, problem, filename):
    DB = problems.get_testcase_for_judging(problemset, problem)
    subtasks = chain(
        [subtask_judge.s(
            filename=filename,
            idx=idx,
            json=tc['json']) for idx, tc in enumerate(DB['testcases'])]
    )
    return subtasks


@celery.task(track_started=True, ignore_result=False)
def subtask_judge(previous_return=None, **kwargs):
    filename = kwargs['filename']
    idx = kwargs['idx']
    json = kwargs['json']
    with open('./UPLOADED/' + filename + '.log', 'wb') as log:
        Validate(
            this_program='./UPLOADED/%s' % (filename,),
            from_json=json,
            logfile=log,
            report=report,
            python=app.config['VIRTUAL_ENV'],
        )
    return 'done %s json %s' % (filename, idx)
# WHENEVER CHANGES HAPPENED FOR CELERY, NEED TO RESTART CELERY!


@app.route('/status/<task_id>/')
def status(task_id):
    _task = celery.AsyncResult(task_id)
    if _task.state == 'STARTED':
        response = {
            'state': _task.state,
            'current': 0,
            'total': 1,
            'statue': 'Started...',
        }
    elif _task.state == 'PENDING':
        response = {
            'state': _task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...',
        }
    elif _task.state == 'SUCCESS':
        response = {
            'state': _task.state,
            'current': 1,
            'total': 1,
            'status': _task.info,
        }
    elif _task.state != 'FAILURE':
        response = {
            'state': _task.state,
            'current': _task.info.get('current', 0),
            'total': _task.info.get('total', 1),
            'status': _task.info.get('status', ''),
        }
    else:
        response = {
            'state': _task.state,
            'current': 1,
            'total': 1,
            'status': str(_task.info),
        }
    return jsonify(response)


@app.route('/')
def index():
    return render_template(
            'index.html',
            problemsets=problems.get_all_sets(),
    ), 200


@app.route('/favicon.ico/')
def favicon():
    return redirect('/static/favicon.ico')


@app.route('/<problemset>/')
def problemset(problemset):
    return render_template(
            'problemset.html',
            problemset=problemset,
            problems=problems.get_problems(problemset),
    ), 200


@app.route('/<problemset>/<problem>/', methods=['GET', 'POST'])
def problem(problemset, problem):
    if request.method == 'GET':
        return render_template(
                'problem.html',
                problemset=problemset,
                problem=problem,
                descrpition=problems.get_problem_description(
                    problemset, problem
                ),
                submit_url=url_for(
                    'problem_submit',
                    problemset=problemset,
                    problem=problem,
                ),
        ), 200
    else:
        return redirect(url_for('submit'), code=307)


@app.route('/<problemset>/<problem>/submit', methods=['GET', 'POST'])
def problem_submit(problemset, problem):
    if request.method == 'GET':
        return redirect(
                url_for('problem', problemset=problemset, problem=problem)
        )
    else:
        filename = submit()
        tasks = task_judge(problemset, problem, filename).delay()
        return jsonify({
            'filename': filename,
            'task_id': tasks.id,
        })


def submit():
    f = request.files['upfile']
    filename = str(uuid.uuid4())
    if not os.path.exists('./UPLOADED/'):
        os.makedirs('./UPLOADED/')
    f.save(os.path.join('./UPLOADED/', filename))

    return filename


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
