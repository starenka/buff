##Wha?

Buff is a supersimple bookmarking app you can stick your links in. You can delete a link and set/unset its read status. No less no more. I just needed something that (dead?) simple plus I wanted to give Bottle a shot.

![buff](https://github.com/starenka/buff/raw/master/screenshot.png)

###Where is a bookmarklet?
You really don't need one. Just `POST` a `url` parameter with your url to `/create`. Config custom search in your [favorite browser](http://www.opera.com/help/tutorials/intro/customize/#searchengine) or use curl or whatever.

##Running

You can ran the app from the commandline with `python ./app.py`, if you want to run it on server, here's sample nginx & uwsgi/supervisor configuration:

###uwsgi:

    [program:buff.starenka.net]
    command=/www/buff/.env/bin/uwsgi
      --chdir=/www/buff
      --home=/www/buff/.env
      --socket=/www/buff/uwsgi.sock
      --touch-reload=/www/buff/reload

      --chmod-socket=666
      --uid=www-data
      --gid=www-data

      --max-requests=2000
      --processes=3
      --procname-prefix-spaced="[www] %(program_name)s"
      --auto-procname
      --master
      --no-orphans

      --file=app.py

    stdout_logfile=/www/buff/uwsgi.log
    user=www-data
    autostart=true
    autorestart=true
    redirect_stderr=true
    stopsignal=QUIT

###nginx:

    server {
        listen       80;
        server_name  buff.starenka.net;
        root        /www/buff/;

        access_log          /www/buff/access.log combined;
        error_log           /www/buff/error.log;
        error_page  500     /www/buff/500.html;

        location / {
            uwsgi_pass              unix:///www/buff/uwsgi.sock;
            include                 uwsgi_params;
            auth_basic              "3UP left";
            auth_basic_user_file    /www/buff/.passwd;
        }
    }
