import requests
import json
from flask import Flask, request
from uuid import uuid4
import os

app = Flask(__name__)
app.secret_key = uuid4().hex


class InvalidException(Exception):
    pass


def verify(upload_token):
    """
    verify an upload token
    :param upload_token: upload token
    :return: file_name
    """

    req = requests.post('http://auth:5001/upload/verify', json={
        "token": upload_token
    })

    if req.status_code != 200:
        raise InvalidException()

    if "file_name" not in req.json():
        raise InvalidException()

    return req.json()['file_name']


def expire_token(upload_token):
    """
    expire upload token
    :param upload_token:
    :return: true
    """

    requests.post('http://auth:5001/upload/expire', json={
        "token": upload_token
    })

    return True


@app.route('/upload/<upload_token>', methods=['GET'])
def upload_form(upload_token):
    return f"""
    <html>
    <form method="post" action="/upload/{upload_token}" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <input type="submit" value="submit">
    </html>
    """


@app.route('/upload/<upload_token>', methods=['POST'])
def upload(upload_token):

    file_name = None

    try:
        file_name = verify(upload_token)
    except InvalidException:
        return "invalid url"
    except Exception as e:
        return str(e)
        return "something went wrong"

    if 'file' not in request.files:
        return "missing file"

    file = request.files['file']
    file.save(os.path.join(f'static/', file_name))
    expire_token(upload_token)
    return "successfully uploaded"


if __name__ == '__main__':

    app.run(host="0.0.0.0", port=5000, debug=True)


