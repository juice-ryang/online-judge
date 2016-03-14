import os
import time
import uuid
from json import load

from celery import (
    Celery,
    chain,
)
from celery.task.http import URL
from flask import (
    Flask,
    session,
    url_for,
    render_template,
    redirect,
    request,
    jsonify,
    current_app,
)
from flaskext.markdown import Markdown
from flask_socketio import SocketIO, emit, join_room, rooms

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
app.config['PORT'] = int(os.environ.get('PORT', 5000))

celery = Celery(app.name)
celery.conf.update(app.config)

socketio = SocketIO(app)
Markdown(app)


def task_judge(problemset, problem, filename):
    DB = problems.get_testcase_for_judging(problemset, problem)
    subtasks = chain(
        [subtask_judge.s(
            filename=filename,
            N=DB['N'],
            idx=idx,
            json=tc['json']) for idx, tc in enumerate(DB['testcases'])]
    )
    return subtasks


# WHENEVER CHANGES HAPPENED FOR CELERY, NEED TO RESTART CELERY!
@celery.task(bind=True, track_started=True, ignore_result=False)
def subtask_judge(self, previous_return=None, **kwargs):
    import requests
    filename = kwargs['filename']
    idx = kwargs['idx']
    json = kwargs['json']
    N = kwargs['N']
    root = "http://localhost:%s" % (app.config['PORT'],)

    if not previous_return:
        requests.post(
            root + "/api/start/",
            data={
                'filename': filename,
                'N': N,
            }
        )

    class JudgeFailed(Exception):
        pass

    reported_stdout = []
    def report(this):
        def _(*args, **kwargs):
            out = this(*args, **kwargs)
            func = this.__name__
            if func == "_START":
                requests.post(
                    root + "/api/start_tc/",
                    data={
                        'filename': filename,
                        'idx': idx,
                    }
                )
            elif func == "_FAIL":
                raise JudgeFailed()
            elif func == "_GOT_STDOUT":
                reported_stdout.append(out)
            return out
        return _

    try:
        with open('./UPLOADED/%s.%s.log' % (filename, idx), 'wb') as log:
            Validate(
                this_program='./UPLOADED/%s' % (filename,),
                from_json=json,
                logfile=log,
                report=report,
                python=app.config['VIRTUAL_ENV'],
            )
    except JudgeFailed as Failed:
        expected = None
        with open(json) as fp:
            stdouts = [stdout for _, stdout in load(fp)]
            expected = ''.join(stdouts)
        data = {
            'filename': filename,
            'idx': idx,
            'status': False,
            'expected': expected,
            'output': ''.join(reported_stdout),
        }
        requests.post(
            root + "/api/testcase/",
            data=data,
        )
        raise Failed
    else:
        data = {
            'filename': filename,
            'idx': idx,
            'status': True,
            'expected': 'nope',
            'output': 'nope',
        }
        requests.post(
            root + "/api/testcase/",
            data=data,
        )
    return data
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
        tasks = task_judge(problemset, problem, filename).apply_async(countdown=1.5)
        return render_template(
                'result.html',
                fileid=filename,
        )


def submit():
    f = request.files['upfile']
    filename = str(uuid.uuid4())
    if not os.path.exists('./UPLOADED/'):
        os.makedirs('./UPLOADED/')
    f.save(os.path.join('./UPLOADED/', filename))

    return filename


@app.route('/result/')
def result():
    return render_template(
            'result.html',
            fileid = "testid!!!",
    ), 200



@app.route('/api/start/', methods=["POST"])
def resulttest():
    emit('start judge',
            {'N': request.form['N']},
            room = request.form['filename'],
            namespace='/test'
    )
    return ''


@app.route('/api/start_tc/', methods=['POST'])
def start_tc():
    emit('start testcase',
            {'idx': request.form['idx']},
            room = request.form['filename'],
            namespace='/test'
    )
    return ''


@app.route('/api/testcase/', methods=['POST'])
def resulttestcase():
    print(request.form)
    output = request.form['output']
    emit('judging testcase', {
                'idx': request.form['idx'],
                'pass': request.form['status'], 
                'expected': request.form['expected'],
                'output': output
                },
            room=request.form['filename'], namespace='/test')
    return ''


app.config['SECRET_KEY'] = 'secret!'
@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])


if __name__ == "__main__":
    import eventlet
    eventlet.monkey_patch()
    socketio.run(app, debug=True, host="0.0.0.0", port=app.config['PORT'])
