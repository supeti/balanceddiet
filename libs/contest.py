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
from urllib.request import urlopen, Request

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
    #install_opener(build_opener(ProxyHandler({})))

def get_gplus_account_id(access_token):
    request = Request('https://www.googleapis.com/oauth2/v1/userinfo?access_token=' + access_token)
    request.add_header('Content-Type', 'application/x-www-form-urlencoded;charset=utf-8')
    args = json.loads(urlopen(request).readall().decode())
    print(args)
    return args['id']

body = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Balanced Diet Contest</title>
    <subtitle>Recent Changes</subtitle>
    <link href="%(site)s/contest/feed" rel="self" />
    <link href="%(site)s" />
    <id>%(site)s</id>
    <updated>%(updated)s</updated>
    <icon>%(site)s/static/Cherry-16.png</icon>
    <logo>%(site)s/static/Cherry-48.png</logo>
%(entries)s
</feed>
"""
site_url = 'http://balanceddiet-supeti.rhcloud.com'

entry = """
        <entry>
                <title>%(title)s</title>
                <id>%(site)s/contest/#%(id)s</id>
                <link rel='alternate' type='text/html' href='%(site)s/contest/#%(id)s'/>
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
          'site': site_url
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
    d['site'] = site_url
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
            rec = {'score':record['contents']['score'], 'rid':rid,
                   'title':record['title'], 'user':record['user']}
            rl.append(rec)
            if max_rid < rid: max_rid = rid
    rl.sort(key=lambda d: (-float(d['score']), int(d['rid'])))
    for i in rl[100:]:
        if 100 - rl[1] < max_rid: os.unlink
    list_response = [ gzip.compress(json.dumps(rl).encode()) ]
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
        header = json_header.copy()
        header[1] = ('Content-Length', str(len(user_records[uid][0])))
        user_headers[uid] = header

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
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar)
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

def delete_user_records(uid, rids):
    urlt = json.loads(gzip.decompress(user_records[uid][0]).decode())
    for rec in urlt:
        rid = str(rec['rid'])
        if rid in rids:
            path = os.path.join(records_path, str(rid) + '.xz')
            os.unlink(path)
            path = os.path.join(feed_path, str(rid) + '.gz')
            os.unlink(path)
    load_records()
    load_feed()

