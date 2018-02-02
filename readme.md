### End about project

* `requests` package we must enter both `http` and `https` for proxies working.

* All ways to using thread with python here `https://code.tutsplus.com/articles/introduction-to-parallel-and-concurrent-programming-in-python--cms-28612`
I using the `Pool` method for concurrency thread.

`pycurl` is not working with thread but `requests` is work

* To avoid error with `requests`

```textmate
File "/root/Env/python/lib/python3.5/encodings/idna.py", line 167, in encode
    raise UnicodeError("label too long")
UnicodeError: label too long
```

We must understand that requests using `url` and `params` so for complete url we must separately as below:

```textmate
from urllib.parse import urlparse, parse_qs
        o = urlparse(url)
        query = parse_qs(o.query)
        url_short = o._replace(query=None).geturl()
        g = session.get(url_short, params=query)
        result = get_html_content(g.content)
```


* For running Django in background cron-tasks. I using custom commands  
 
 Read more at  `https://docs.djangoproject.com/en/2.0/howto/custom-management-commands/#management-commands-and-locales`.
 
For using Virtualenv at Cronjob, Edit `/etc/crontab` : 

```textmate
* * * * * root  /root/Env/python/bin/python /var/www/python/manage.py click >> /dev/null 2>&1
```