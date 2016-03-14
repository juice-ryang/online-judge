from OnlineJudgeServer import (
    app,
    celery,
    socketio,
)


if __name__ == "__main__":
    import eventlet
    eventlet.monkey_patch()
    socketio.run(app, debug=True, host="0.0.0.0", port=app.config['PORT'])
