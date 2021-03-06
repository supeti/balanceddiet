#!/usr/bin/env python
import imp
import os
import os.path

#try:
#   zvirtenv = os.path.join(os.environ['OPENSHIFT_PYTHON_DIR'],
#                           'virtenv', 'bin', 'activate_this.py')
#   exec(compile(open(zvirtenv).read(), zvirtenv, 'exec'),
#        dict(__file__ = zvirtenv) )
#except IOError:
#   pass

for root, dirs, files in os.walk('/opt/app-root/src', topdown=False):
    for name in files:
        print(os.path.join(root, name))
print('workdir:', os.getcwd())

def run_simple_httpd_server(app, ip, port=8080):
   from wsgiref.simple_server import make_server
   make_server(ip, port, app).serve_forever()

#
# IMPORTANT: Put any additional includes below this line.  If placed above this
# line, it's possible required libraries won't be in your searchable path
#

#
#  main():
#
if __name__ == '__main__':
   #ip   = os.environ['OPENSHIFT_PYTHON_IP']
   #port = int(os.environ['OPENSHIFT_PYTHON_PORT'])
   zapp = imp.load_source('application', 'wsgi/application')

   print('Starting WSGIServer on %s:%d ... ' % ('', 8080))
   run_simple_httpd_server(zapp.application, '', 8080)


