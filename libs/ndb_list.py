#!/usr/bin/env python

import lzma
import os

groups = {}
with lzma.open('food_groups.xz', 'rt', encoding='utf8') as input_file:
    for l in input_file:
        a = l.strip().split('|')
        groups[a[0]] = a[1]

foods = {}
with lzma.open('food_desc.xz', 'rt', encoding='utf8') as input_file:
    for l in input_file:
        a = l.strip().split('|')
        if a[1] in foods:
            foods[a[1]].append((a[0], a[2]))
        else:
            foods[a[1]] = [(a[0], a[2])]

begin = '''<!DOCTYPE html>
<html lang="en">
<head>
  <title>Balanced Diet - List of Food Items</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <link rel="shortcut icon" href="/static/Cherry-16.png" type="image/png">
  <link rel="stylesheet" type="text/css" href="/static/main.css">
  <link rel='stylesheet' type='text/css' href='http://fonts.googleapis.com/css?family=Berkshire+Swash|Tienne:700|Istok+Web:400,400italic,700,700italic'>
  <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>
</head>

<body>
  <h1>List of Food Items</h1>
'''

end = '</body>'

with open('ndb_list.html', 'wt') as output:
    output.write(begin)
    for gid in sorted(groups.keys()):
        output.write('  <h2>%s %s</h2>\n' % (gid, groups[gid]))
        for fid,fdesc in sorted(foods[gid]):
            output.write('    <p>%s %s</p>\n' % (fid , fdesc))
    output.write(end)

