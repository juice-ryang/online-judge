from OnlineJudgeServer import (
    app,
    celery,
)


if __name__ == "__main__":
    import eventlet
    eventlet.monkey_patch()
    app.run(debug=True, host="0.0.0.0", port=app.config['PORT'])
