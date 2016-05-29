from OnlineJudgeServer import (
    app,
    celery,
)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
