from flask import (
    Flask,
)

import problems

app = Flask(__name__)


@app.route('/')
def index():
    return "helloworld"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
