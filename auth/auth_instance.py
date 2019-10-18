from flask import Flask, abort, request, jsonify
from uuid import uuid4
from redis import Redis
import json
import ntpath


redis = Redis(host="redis")
app = Flask(__name__)


class InvalidKey(Exception):
    pass


def cache_and_token(section, data, ttl):
    """
    cache value and create token
    :param section: token section
    :param data: token data json:
    :param ttl: time to live
    :return: token
    """

    token = uuid4().hex
    redis.set(name=f"{section}:{token}", value=json.dumps(data), ex=ttl)
    return token


def get_cache(section, key):
    """
    get cached value as json
    :param section: cache section
    :param key: key for value
    :return: json
    """

    data = redis.get(f'{section}:{key}')
    if not data:
        raise InvalidKey()

    return json.loads(data)


def delete_cache(section, key):
    """
    delete cache
    :param section: cache section
    :param key: key for value
    :return: true
    """

    redis.delete(f'{section}:{key}')
    return True


def format_ttl(ttl, default, max):
    """
    format ttl value
    :param ttl: ttl value
    :param default: default value
    :param max: max value
    :return: ttl value as int
    """

    if not ttl:
        return default

    try:
        ttl = int(ttl)
    except:
        return default

    if ttl > max:
        return max

    return ttl


@app.route('/upload/verify', methods=['POST'])
def upload_verify_url():

    if not request.json:
        return abort(400)

    token = request.json.get('token')
    if not token:
        return abort(404)

    try:
        data = get_cache('upload', token)
        return jsonify({
            "ok": True,
            "file_name": data['file_name']
        })
    except InvalidKey:
        return abort(404)


@app.route('/upload/expire', methods=['POST'])
def upload_expire_url():
    if not request.json:
        return abort(400)

    token = request.json.get('token')
    if not token:
        return abort(404)

    delete_cache('upload', token)
    return jsonify({'ok': True})


@app.route('/download/verify', methods=['GET'])
def download_verify_url():

    file_name = ntpath.basename(request.headers.get("X-Original-Uri"))
    token = request.headers.get('Authorization')

    if not token:
        return abort(404)

    try:
        data = get_cache("download", token)
        if not data['file_name'] == file_name:
            return abort(404)
        return jsonify({
            "ok": True,
            "file_name": data['file_name']
        })
    except InvalidKey:
        return abort(404)


@app.route('/upload/sign_url', methods=['POST'])
def upload_sign_url():

    if not request.json:
        return abort(400)

    file_name = request.json.get('file_name')
    ttl = format_ttl(ttl=request.json.get('ttl'), default=604800, max=604800)

    if not file_name:
        return abort(400)

    token = cache_and_token("upload", data={'file_name': file_name}, ttl=ttl)

    return jsonify({
        "ok": True,
        "token": token,
        "ttl": ttl,
        "file_name": file_name
    })


@app.route('/download/sign', methods=['POST'])
def down_sign_url():

    if not request.json:
        return abort(400)

    file_name = request.json.get('file_name')
    ttl = format_ttl(ttl=request.json.get('ttl'), default=604800, max=604800)

    if not file_name:
        return abort(400)

    token = cache_and_token("download", data={'file_name': file_name}, ttl=ttl)

    return jsonify({
        "ok": True,
        "token": token,
        "ttl": ttl,
        "file_name": file_name
    })


if __name__ == '__main__':

    app.run(host="0.0.0.0", port=5001, debug=True)
