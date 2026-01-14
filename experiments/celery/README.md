# How to run example --> https://flask.palletsprojects.com/en/stable/patterns/celery/

1. start server in celery directory via
```bash
flask -A src.task_app run --debug
```

2. start redis with
```bash
docker run -p 6379:6379 redis
```

3. windows supported to start celery workers, see more: https://celery.school/celery-on-windows
Note: --pool=threads is not production-equivalent, on linux use prefork for production
```bash
celery -A make_celery worker  --pool=threads  --concurrency=8  --loglevel=DEBUG  -E
```