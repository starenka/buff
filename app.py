#!/usr/bin/env python
# coding=utf-8

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
    url = url.strip()
    try:
        r = requests.get(url, timeout=30, stream=False, verify=False)
        soup = BeautifulSoup(r.content)
        title, h1 = soup.title.string, soup.find('h1').text
        return unicode(title or h1)
    except (AttributeError, requests.exceptions.Timeout) as e:
        return url[:70] + u'…'

def get_links(rdb, key=KEY_IN):
    hashes = rdb.lrange(key, 0, rdb.llen(key))
    return zip(hashes, map(jsonpickle.decode, rdb.hmget(KEY_LINKS, *hashes))) if hashes else []

@get('/in')
@get('/')
def unread(rdb):
    return template('unread.html', links=list(get_links(rdb, KEY_IN)), in_=True, title='In')

@get('/read')
def read(rdb):
    return template('read.html', links=list(get_links(rdb, KEY_READ)), read_=True, title='Read')

@post('/create')
def add(rdb):
    url = request.forms.get('url')
    hash = hashlib.sha224(url).hexdigest()
    ihas = rdb.hget(KEY_LINKS, hash)
    if not ihas:
        rec = dict(url=url, stamp=datetime.datetime.now(), title=get_url_title(url))
        rdb.hset(KEY_LINKS, hash, jsonpickle.encode(rec))
        rdb.lpush(KEY_IN, hash)
    item = jsonpickle.decode(ihas) if ihas else rec
    return template('new.html', is_new=not ihas, item=item, title='New link')

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

@post('/search')
def search(rdb): #poor man's search (i don't need zsets/acs now)
    def _search(term, links):
        term = term.lower()

        return {'title': filter(lambda x: x[1]['title'] and term in x[1]['title'].lower(), links),
                'url': filter(lambda x: term in x[1]['url'].lower(), links)}

    term = unicode(request.forms.get('term').decode('utf8'))
    title = u'Results for %s' % term
    unread = _search(term, get_links(rdb, key=KEY_IN))
    read = _search(term, get_links(rdb, key=KEY_READ))

    return template('search.html', title=title, term=term, read=read, unread=unread)


if __name__ == '__main__':
    from werkzeug.debug import DebuggedApplication
    app = app()
    app.catchall = False
    application = DebuggedApplication(app, evalex=True)
    run(app=application, host='localhost', port=8080, reloader=True, debug=True)
else:
    application = default_app()
