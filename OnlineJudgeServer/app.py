import os
import time

from celery import Celery
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
from terminal_capsule import Validate

app = Flask(__name__)
app.config['CELERY_ACCEPT_CONTENT'] = ['json']
app.config['CELERY_TASK_SERIALIZER'] = 'json'
app.config['CELERY_RESULT_SERIALIZER'] = 'json'
app.config['CELERY_TIMEZONE'] = 'Asia/Seoul'
app.config['CELERY_BROKER_URL'] = 'amqp://guest@localhost//'
app.config['CELERY_RESULT_BACKEND'] = app.config['CELERY_BROKER_URL']
app.config['VIRTUAL_ENV'] = os.environ.get('VIRTUAL_ENV')

celery = Celery(
        app.name,
        # broker=app.config['CELERY_BROKER_URL'],
        # backend=app.config['CELERY_RESULT_BACKEND'],
)
celery.conf.update(app.config)


Markdown(app)


@celery.task(ignore_result=True)
def task_test(a, b):
    return a+b


@celery.task(ignore_result=True)
def task_judge(problemset, problem, filename):
    with open(filename + '.log', 'wb') as log:
        Validate(
            this_program='./UPLOADED/%s' % (filename,),
            from_json='test.json',  # 12, 2
            logfile=log,
        )
    return 'done'


@app.route('/celery/task_test/')
def celery_task_test():
    return task_test.delay(10, 20).id


@app.route('/status/<task_type>/<task_id>/')
def status(task_type, task_id):
    if task_type == "task_test":
        task = task_test
    elif task_type == "task_judge":
        task = task_judge
    else:
        return 'Not Found', 404
    _task = task.AsyncResult(task_id)
    if _task.state == 'PENDING':
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
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(_task.info),
        }
    return jsonify(response)


@app.route('/')
def index():
    return render_template(
            'index.html',
            problemsets = problems.get_all_sets()
    ), 200


@app.route('/favicon.ico/')
def favicon():
    return redirect('/static/favicon.ico')


@app.route('/<problemset>/')
def problemset(problemset):
    return render_template(
            'problemset.html',
            problemset = problemset,
            problems = problems.get_problems(problemset)
    ), 200


@app.route('/<problemset>/<problem>/', methods=['GET', 'POST'])
def problem(problemset, problem):
    if request.method == 'GET' :
        return render_template(
                'problem.html',
                problemset = problemset,
                problem = problem,
                descrpition = problems.get_problem_description(problemset, problem),
                submit_url = url_for('problem_submit', problemset=problemset, problem=problem),
        ), 200
    else :
        return redirect(url_for('submit'), code=307)


@app.route('/<problemset>/<problem>/submit', methods=['GET', 'POST'])
def problem_submit(problemset, problem):
    if request.method == 'GET':
        return redirect(url_for('problem', problemset=problemset, problem=problem))
    else:
        filename = submit()
        task_id = task_judge.delay(problemset, problem, filename).id
        return jsonify({
            'filename': filename,
            'task_id': task_id,
        })


#@app.route('/submit/', methods=['POST'])
def submit():
    f = request.files['upfile']
    filename = str(time.time())
    if not os.path.exists('./UPLOADED/'):
        os.makedirs('./UPLOADED/')
    f.save(os.path.join('./UPLOADED/', filename))

    return filename


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
