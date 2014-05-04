import hashlib, datetime

from bottle import (get, post, request, run, default_app, app, install,
            redirect, TEMPLATE_PATH, jinja2_template as template)
import bottle_redis, jsonpickle, requests

from bs4 import BeautifulSoup

plugin = bottle_redis.RedisPlugin(host='localhost')
install(plugin)

KEY_IN, KEY_READ, KEY_LINKS = 'BUFF_in', 'BUFF_read', 'BUFF_links'
TEMPLATE_PATH.append('./templates')

def get_url_title(url):
    try:
        r = requests.get(url, timeout=30, stream=False, verify=False)
        soup = BeautifulSoup(r.content)
        return unicode(soup.title.string)
    except (AttributeError, requests.exceptions.Timeout) as e:
        return None

def get_links(rdb, key=KEY_IN):
    hashes = rdb.lrange(key, 0, rdb.llen(key))
    return zip(hashes, map(jsonpickle.decode, rdb.hmget(KEY_LINKS, *hashes))) if hashes else []

@get('/in')
@get('/')
def unread(rdb):
    return template('unread.html', links=list(get_links(rdb, KEY_IN)), in_=True, title='In')

@get('/read')
def read(rdb):
    return template('read.html', links=list(get_links(rdb, KEY_READ)), read=True, title='Read')

@post('/create')
def add(rdb):
    url = request.forms.get('url')
    hash = hashlib.sha224(url).hexdigest()
    is_new = not rdb.hexists(KEY_LINKS, hash)
    if is_new:
        rec = dict(url=url, stamp=datetime.datetime.now(), title=get_url_title(url))
        rdb.hset(KEY_LINKS, hash, jsonpickle.encode(rec))
        rdb.lpush(KEY_IN, hash)
    return template('new.html', is_new=is_new, url=url, title='New link')

@get('/add')
def add_form():
    return template('add.html', title='Add URL', add_=True)


@get('/set-read/<hash>')
def setread(hash, rdb):
    rdb.lrem(KEY_IN, hash)
    rdb.lpush(KEY_READ, hash)
    redirect('/read')

@get('/set-unread/<hash>')
def setunread(hash, rdb):
    rdb.lrem(KEY_READ, hash)
    rdb.lpush(KEY_IN, hash)
    redirect('/in')

@get('/del/<hash>')
def delete(hash, rdb):
    rdb.lrem(KEY_READ, hash)
    rdb.lrem(KEY_IN, hash)
    rdb.hdel(KEY_LINKS, hash)
    redirect('/in')


if __name__ == '__main__':
    from werkzeug.debug import DebuggedApplication
    app = app()
    app.catchall = False
    application = DebuggedApplication(app, evalex=True)
    run(app=application, host='localhost', port=8080, reloader=True, debug=True)
else:
    application = default_app()
