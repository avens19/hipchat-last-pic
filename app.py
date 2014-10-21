import re
import urlparse
import subprocess

import requests
from flask import Flask, render_template, jsonify, abort
from werkzeug.contrib.cache import SimpleCache

from settings import token, room_id


picture_regexp = re.compile("(.*[\s/])?(?P<url>[^\s]+\.[A-Za-z0-9]{2,8}/[^\s]+(jpe?g|png|gif))$", re.IGNORECASE)

auth_params = {'auth_token': token}

app = Flask(__name__, template_folder='')

cache = SimpleCache()


def get_cached_url():
    # look in cache
    url = cache.get('pic_url')
    if url is None:
        url = get_pic_from_hipchat()
        cache.set('pic_url', url, timeout=10)
    return url


def get_pic_from_hipchat():
    # get last messages
    r = requests.get("http://api.hipchat.com/v2/room/{}/history/latest".format(room_id), params=auth_params)

    # if there is no 'items' key then something went wrong
    if not 'items' in r.json().keys():
        return abort(502)

    url = None

    # find last image url
    for message in reversed(r.json()['items']):
        result = picture_regexp.match(message['message'])
        if result:
            url = result.group('url')
            break

    if url is None:
        # no messages with pic url in this room
        return abort(404)

    # make url absolute
    u = urlparse.urlparse(url)
    if not u.scheme:
        url = "http://{}".format(u.geturl())

    return url


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/get_last_pic_url")
def last_pic_url():
    return jsonify({'url': get_cached_url()})


@app.route("/version")
def version():
    commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()
    return jsonify({'version': commit_hash})

if __name__ == "__main__":
    app.run(debug=True)
