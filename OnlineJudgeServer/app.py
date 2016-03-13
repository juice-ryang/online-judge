import os
import time

from flask import (
    Flask,
    url_for,
    render_template,
    redirect,
    request,
)
from flaskext.markdown import Markdown

import problems

app = Flask(__name__)

Markdown(app)

@app.route('/')
def index():
    return render_template(
            'index.html',
            problemsets = problems.get_all_sets()
    ), 200

@app.route('/favicon.ico')
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
                descrpition = problems.get_problem_description(problemset, problem)
        ), 200
    else :
        return redirect(url_for('submit'), code=307)

@app.route('/submit', methods=['POST'])
def submit():
    f = request.files['upfile']
    filename = str(time.time())
    if not os.path.exists('./UPLOADED/'):
        os.makedirs('./UPLOADED/')
    f.save(os.path.join('./UPLOADED/', filename))

    return 'submit!'

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
