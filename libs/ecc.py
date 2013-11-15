#!/usr/bin/env python

import codecs
import datetime
import gzip
import json
import lzma
import os
import pickle
import tarfile
from html.parser import HTMLParser
from urllib.parse import urlencode
from urllib.request import urlopen, build_opener, install_opener
from urllib.request import HTTPHandler, ProxyHandler, Request

records = {}
list_response = []
max_rid = 0

json_header = [('Content-Type', 'application/json; charset=UTF-8'),
               ('Content-Length', None),
               ('Content-Encoding', 'gzip')]
feed_header = [('Content-Type', 'application/atom+xml; charset=UTF-8'),
               ('Content-Length', None),
               ('Content-Encoding', 'gzip')]

def init(data_dir):
    global data_path
    data_path = data_dir
    global feed_path
    feed_path = os.path.join(data_path, 'feed')
    if not os.path.isdir(feed_path): os.makedirs(feed_path)
    global records_path
    records_path = os.path.join(data_path, 'records')
    if not os.path.isdir(records_path): os.makedirs(records_path)
    load_feed()
    load_records()

def get_gplus_account_id(access_token):
    request = Request('https://www.googleapis.com/oauth2/v1/userinfo?access_token=' + access_token)
    request.add_header('Content-Type', 'application/x-www-form-urlencoded;charset=utf-8')
    args = json.loads(urlopen(request).readall().decode())
    return args['id']

body = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Extreme Cooking Contest</title>
    <subtitle>Recent Changes</subtitle>
    <link href="http://ecc-supeti.rhcloud.com/feed" rel="self" />
    <link href="http://ecc-supeti.rhcloud.com" />
    <id>http://ecc-supeti.rhcloud.com/</id>
    <updated>%(updated)s</updated>
    <icon>http://ecc-supeti.rhcloud.com/static/ECC-16.png</icon>
    <logo>http://ecc-supeti.rhcloud.com/static/ECC-60.png</logo>
%(entries)s
</feed>
"""

entry = """
        <entry>
                <title>%(title)s</title>
                <id>http://ecc-supeti.rhcloud.com/#%(id)s</id>
                <link rel='alternate' type='text/html' href='http://ecc-supeti.rhcloud.com/#%(id)s'/>
                <updated>%(updated)s</updated>
                <summary>%(summary)s</summary>
                <author>
                      <name>%(name)s</name>
                      <uri>%(author_uri)s</uri>
                </author>
                <content type="html">%(content)s</content>
        </entry>
"""

def dump_feed_entry(e, rid):
    user = e['user']
    score = 'score: ' + e['contents']['score']
    d = { 'title': e['title'],
          'id': rid,
          'updated': datetime.datetime.utcnow().isoformat() + 'Z',
          'summary': e['comments'],
          'name': user['displayName'],
          'author_uri': user['url'],
          'content': score,
        }
    path = os.path.join(feed_path, str(rid) + '.gz')
    with gzip.open(path, 'wb') as f:
        f.write((entry % d).encode())

def load_feed():
    entries = []
    cwd = os.getcwd()
    os.chdir(feed_path)
    files = os.listdir()
    files.sort(reverse=True)
    while 100 < len(files): os.unlink(files.pop())
    for fn in files:
        with gzip.open(fn, 'rb') as f:
            entries.append(f.read().decode())
    os.chdir(cwd)
    d = {}
    d['updated'] = datetime.datetime.utcnow().isoformat() + 'Z'
    d['entries'] = ''.join(entries)
    feed = gzip.compress((body % d).encode())
    feed_header[1] = ('Content-Length', str(len(feed)))
    global feed_response
    feed_response = [ feed ]

def dump_record(rid, record):
    record['rid'] = rid
    path = os.path.join(records_path, str(rid) + '.xz')
    with lzma.open(path, 'wb') as f:
        pickle.dump(record, f)

def load_records():
    global list_header
    global list_response
    global max_rid
    global user_records
    global user_headers
    records.clear()
    cwd = os.getcwd()
    print(records_path)
    os.chdir(records_path)
    files = os.listdir()
    max_rid = 0
    rl = []
    for fn in files:
        with lzma.open(fn, 'rb') as f:
            record = pickle.load(f)
            rid = record['rid']
            response = gzip.compress(json.dumps(record).encode())
            header = json_header.copy()
            header[1] = ('Content-Length', str(len(response)))
            records[rid] = (header, [response])
            print(str(record['user']['id']))
            rec = {'score':record['contents']['score'], 'rid':rid,
                   'title':record['title'], 'user':record['user']}
            rl.append(rec)
            if max_rid < rid: max_rid = rid
    rl.sort(key=lambda d: (-float(d['score']), int(d['rid'])))
    for i in rl[100:]:
        if 100 - rl[1] < max_rid: os.unlink
    list_response = [ gzip.compress(json.dumps(rl).encode()) ]
    print(json.dumps(rl).encode())
    print(list_response)
    list_header = json_header.copy()
    list_header[1] = ('Content-Length', str(len(list_response[0])))
    os.chdir(cwd)
    urlt = {}
    user_headers = {}
    user_records = {}
    for rec in rl:
        uid = rec['user']['id']
        if not uid in urlt.keys():
            urlt[uid] = []
        urlt[uid].append(rec)
    for uid in urlt.keys():
        user_records[uid] = [ gzip.compress(json.dumps(urlt[uid]).encode()) ]
        list_header = json_header.copy()
        list_header[1] = ('Content-Length', str(len(urlt[uid][0])))
        user_headers[uid] = list_header

def add_record(d):
    global max_rid
    max_rid += 1
    dump_record(max_rid, d)
    load_records()
    dump_feed_entry(d, max_rid)
    load_feed()

def backup():
    cwd = os.getcwd()
    os.chdir(data_path)
    archive = 'backup.tar.xz'
    with tarfile.open(archive, "w:xz") as tar:
        tar.add('feed')
        tar.add('records')
    os.chdir(cwd)
    return os.path.join(data_path, archive)

def restore(fn):
    reset()
    cwd = os.getcwd()
    with tarfile.open(fn, "r:xz") as tar:
        os.chdir(data_path)
        tar.extractall()
    os.chdir(cwd)
    load_records()
    load_feed()

def reset():
    cwd = os.getcwd()
    os.chdir(feed_path)
    for fn in os.listdir(): os.unlink(fn)
    os.chdir(records_path)
    for fn in os.listdir(): os.unlink(fn)
    os.chdir(cwd)
