#### Reset migration Django
```textmate
https://simpleisbetterthancomplex.com/tutorial/2016/07/26/how-to-reset-migrations.html

apt-get install libcurl4-openssl-dev


```

* Run the task manually

Assuming the task is called `my_task` in Django app `myapp` in a tasks submodule:

```textmate
$ python manage.py shell
>>> from myapp.tasks import my_task
>>> my_task.delay()

>>> result = machine.delay()
>>> print(backend.result)
```

This will post the task to queue as we defined (Redis, RabbitMQ).

And if we have process daemon running `celery -A project_name worker -l info -B`.

It will execute task queue in Message Broker and result response.

* Another way to debug tasks is `http://docs.celeryproject.org/en/latest/userguide/debugging.html`

* Option for `eventlet` : `-P eventlet -c 1000` but must remove `-B`.

```textmate
insert into python_logs (id, link, agent, allow, country, response, sent) SELECT id, link, '', allow, country, '', sent from logs where sent is null
```

* Delete all queue in `celery`

```textmate
celery -A python_lumen purge

Clear Redis
redis-cli flushall
```

* Crontab
```textmate
run every mins
crontab(minute=0, hour='*/1')
```

* Read

```textmate
https://simpleisbetterthancomplex.com/tutorial/2017/08/20/how-to-use-celery-with-django.html
https://code.tutsplus.com/tutorials/using-celery-with-django-for-background-task-processing--cms-28732
https://www.rabbitmq.com/install-debian.html
http://celery.readthedocs.io/en/latest/tutorials/task-cookbook.html#ensuring-a-task-is-only-executed-one-at-a-time
http://celery.readthedocs.io/en/latest/userguide/tasks.html#performance-and-strategies
https://www.caktusgroup.com/blog/2014/09/29/celery-production/
https://medium.com/@yehandjoe/celery-4-periodic-task-in-django-9f6b5a8c21c7
http://michal.karzynski.pl/blog/2014/05/18/setting-up-an-asynchronous-task-queue-for-django-using-celery-redis/
http://django-background-tasks.readthedocs.io/en/latest/
http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-accept_content
https://stackoverflow.com/questions/40358560/celery-group-task-attributeerror-nonetype-object-has-no-attribute-app
https://stackoverflow.com/questions/7585435/best-way-to-convert-string-to-bytes-in-python-3
http://docs.celeryproject.org/en/v4.0.2/userguide/periodic-tasks.html#beat-custom-schedulers
https://github.com/celery/celery/blob/master/examples/eventlet/webcrawler.py
http://celery.readthedocs.io/en/latest/userguide/optimizing.html#prefork-pool-prefetch-settings
https://medium.com/@taylorhughes/three-quick-tips-from-two-years-with-celery-c05ff9d7f9eb
```
* Why cant use beat with event
```textmate
The embedded beat option simply starts beat as a child process, changing that to use a greenthread on eventlet/geven is not on my todo but I wouldn't reject a patch. It's not recommended that you use -B in production anyway, since it makes it hard to ensure only one is started.
```

* Control RabbitMQ

To enable RabbitMQ Management Console, run the following:
```textmate

sudo rabbitmq-plugins enable rabbitmq_management

# To start the service:
service rabbitmq-server start

# To stop the service:
service rabbitmq-server stop

# To restart the service:
service rabbitmq-server restart

# To check the status:
service rabbitmq-server status

```
Once you've enabled the console, it can be accessed using your favourite web browser by visiting: `http://[your droplet's IP]:15672/`.

* Delete queue in RabbitMQ `http://115.146.123.46:15672/#/queues`

