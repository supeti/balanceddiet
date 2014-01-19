#!/usr/bin/env python

from os import access, R_OK
from os.path import join
from urllib.request import urlopen, Request
import datetime
import gzip
import json
import lzma
import pickle

home_url = "http://balanceddiet-supeti.rhcloud.com/"
badge_class = {
    "name": "Balanced Diet Expert Badge",
    "description": "For demonstrating the ability of using the Balanced Diet Nutrient Calculator.",
    "image": home_url + "static/BDE-badge.png",
    "criteria": home_url + "calculator#certification",
    "tags": ["balanced", "diet", "economized"],
    "issuer": home_url + "calculator/ref/issuer",
}

issuer = {
    "name": "Balanced Diet Community",
    "image": home_url + "static/Cherry-512.png",
    "url": "https://plus.google.com/u/0/communities/100680827449853706792",
    "email": "sulyokpeti@gmail.com",
    "revocationList": home_url + "calculator/ref/revoked"
}

revoked = {}

badge_instance = {
  "uid": None,
  "recipient": {
    "type": "email",
    "hashed": False,
    "identity": "RECIPIENT@DOMAIN.COM"
  },
  "issuedOn": "1389331638",
  "badge": home_url + "calculator/ref/badge_class",
  "verify": {
    "type": "hosted",
    "url": home_url + "calculator/badges/0"
  }
}

def load_badges():
    global badges
    with lzma.open(badges_arch, 'rb') as f:
        badges = pickle.load(f)
    for i in range(len(badges)):
        badges_dict[badges[i][0]] = i

def save_badges():
    with lzma.open(badges_arch, 'wb') as f:
        pickle.dump(badges, f)

def init(data_dir):
    global badges
    global badges_dict
    badges_dict = {}
    global badges_arch
    badges_arch = join(data_dir, 'badges/BDE.xz')
    if access(badges_arch, R_OK):
        load_badges()
    else:
        badges = []
    

persona_url = 'https://verifier.login.persona.org/verify'
#local_url = 'localhost'
def verify_persona(assertion):
    data = { 'assertion': assertion, 'audience': home_url }
    request = Request(persona_url, json.dumps(data).encode('UTF-8'))
    request.add_header('Content-Type', 'application/json;charset=utf-8')
    return json.loads(urlopen(request).readall().decode())

badge_url_tmpl = home_url + "calculator/badges/%s"
badge_cb_tmpl = home_url + "calculator/badgecallback/%s"

def issue_badge(assertion):
    response = {}
    creds = verify_persona(assertion.strip('"'))
    print(creds)
    if creds['status'] == 'okay':
        email = creds['email']
        if email in badges_dict:
            response['result'] = 'old'
            response['badge_url'] = badge_url_tmpl % badges_dict[email]
            #response['badge_callback'] = badge_cb_tmpl % badges_dict[email]
        else:
            badge_id = len(badges)
            time = int(datetime.datetime.today().timestamp())
            badges.append((email, time))
            response['result'] = 'new'
            response['badge_url'] = badge_url_tmpl % badge_id
            #response['badge_callback'] = badge_cb_tmpl % badge_id
            badges_dict[email] = badge_id
            save_badges()
    else:
        response['result'] = 'error'
        response['message'] = creds['reason']
    return json.dumps(response)
    
def get_badge(badge_id):
    response = {}
    bid = int(badge_id)
    if bid < len(badges):
        email, ts = badges[bid]
        badge_instance['uid'] = badge_id
        badge_instance['recipient']['identity'] = email
        badge_instance['issuedOn'] = ts
        badge_instance['verify']['url'] = badge_url_tmpl % badge_id
        response['result'] = 'success'
        response['badge'] = badge_instance
    else:
        response['result'] = 'faliure'
        response['message'] = 'unkown badge ID'
    return json.dumps(response)

def backup():
    return badges_arch

def restore(datafn):
    global badges
    with lzma.open(datafn, 'rb') as f:
        badges = pickle.load(f)
    print(badges)
    save_badges()
    load_badges()

