from flask import (
    Flask,
    render_template,
)
from flaskext.markdown import Markdown

import problems

app = Flask(__name__)

Markdown(app)

@app.route('/')
def index():
    return render_template(
            "index.html",
            problemsets = problems.get_all_sets()
    ), 200


@app.route('/<problemset>/')
def problemset(problemset):
    return render_template(
            "problemset.html",
            problemset = problemset,
            problems = problems.get_problems(problemset)
    ), 200


@app.route('/<problemset>/<problem>/')
def problem(problemset, problem):
    return render_template(
            "problem.html",
            problemset = problemset,
            problems = problem,
            descrpition = problems.get_problem_description(problemset, problem)
    ), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
