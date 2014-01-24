#!/usr/bin/env python

from os import access, mkdir, R_OK
from os.path import isdir,join
from urllib.request import urlopen, Request
import datetime
import gzip
import json
import lzma
import pickle


home_url = "http://balanceddiet-supeti.rhcloud.com/"


class Badger(object):
    def __init__(self, data_dir, name):
        self.badges = {}
        self.badges_dict = {}
        badges_dir = join(data_dir, 'badges')
        if not isdir(badges_dir): mkdir(badges_dir)
        self.badges_arch = join(badges_dir, name + '.xz')
        if access(self.badges_arch, R_OK):
            self.load()
        else:
            self.badges = []
            self.save()

    def load(self):
        with lzma.open(self.badges_arch, 'rb') as f:
            self.badges = pickle.load(f)
        for i in range(len(self.badges)):
            self.badges_dict[self.badges[i][0]] = i

    def save(self):
        with lzma.open(self.badges_arch, 'wb') as f:
            pickle.dump(self.badges, f)

    def issue_badge(self, assertion):
        response = {}
        creds = verify_persona(assertion.strip('"'))
        print(creds)
        if creds['status'] == 'okay':
            email = creds['email']
            if email in badges_dict:
                response['result'] = 'old'
                response['badge_url'] = self.badges_url + badges_dict[email]
            else:
                badge_id = len(badges)
                time = int(datetime.datetime.today().timestamp())
                self.badges.append((email, time))
                response['result'] = 'new'
                response['badge_url'] = self.badges_url + badge_id
                self.badges_dict[email] = badge_id
                save_badges()
        else:
            response['result'] = 'error'
            response['message'] = creds['reason']
        return json.dumps(response)
    
    def get_badge(self, badge_id):
        bid = int(badge_id)
        if bid < len(self.badges):
            email, ts = self.badges[bid]
            self.badge_instance['uid'] = badge_id
            self.badge_instance['recipient']['identity'] = email
            self.badge_instance['issuedOn'] = ts
            self.badge_instance['verify']['url'] = self.badges_url + badge_id
            return json.dumps(self.badge_instance)
        else:
            return '{}'

    def backup(self):
        return self.badges_arch

    def restore(self, datafn):
        with lzma.open(datafn, 'rb') as f:
            self.badges = pickle.load(f)
        print(self.badges)
        self.save()
        self.load()


class BDE(Badger):
    badges_url = home_url + "calculator/badges/"
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
        "url": home_url,
        "email": "sulyokpeti@gmail.com",
        "revocationList": home_url + "calculator/ref/revoked"
    }
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
    revoked = {}
    def __init__(self, data_dir):
        super().__init__(data_dir, 'BDE')


class BDC(Badger):
    badges_url = home_url + "contest/badges/"
    badge_class = {
        "name": "Balanced Diet Contest Badge",
        "description": "For participating in the Balanced Diet Contest.",
        "image": home_url + "static/BDC-badge.png",
        "criteria": home_url + "contest#badge",
        "tags": ["balanced", "diet", "economized"],
        "issuer": home_url + "contest/ref/issuer",
    }
    issuer = {
        "name": "Balanced Diet Community",
        "image": home_url + "static/Cherry-512.png",
        "url": home_url,
        "email": "sulyokpeti@gmail.com",
        "revocationList": home_url + "contest/ref/revoked"
    }
    badge_instance = {
        "uid": None,
        "recipient": {
            "type": "email",
            "hashed": False,
            "identity": "RECIPIENT@DOMAIN.COM"
        },
        "issuedOn": "1389331638",
        "badge": home_url + "contest/ref/badge_class",
        "verify": {
            "type": "hosted",
            "url": home_url + "contest/badges/0"
        }
    }
    revoked = {}
    def __init__(self, data_dir):
        super().__init__(data_dir, 'BDC')


    

persona_url = 'https://verifier.login.persona.org/verify'
#local_url = 'localhost'
def verify_persona(assertion):
    data = { 'assertion': assertion, 'audience': home_url }
    request = Request(persona_url, json.dumps(data).encode('UTF-8'))
    request.add_header('Content-Type', 'application/json;charset=utf-8')
    return json.loads(urlopen(request).readall().decode())



