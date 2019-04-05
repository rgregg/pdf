import os
import shutil
import requests
import subprocess

from gevent.pywsgi import WSGIServer
from flask import Flask, after_this_request, render_template, request, send_file
from subprocess import Popen, PIPE, STDOUT
from timeit import default_timer as timer

app = Flask(__name__)


def calculate_pi(digits):
    input = 'scale=' + str(digits) + '; 4*a(1)\n'
    cmd = ['/usr/bin/bc -l']
    p = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE, text=True, shell=True)
    out, err = p.communicate(input)
    if err:
        print('error calculating: ', err)

    translation_table = dict.fromkeys(map(ord, '\\'), None)
    out = out.translate(translation_table)
    return out


@app.route('/', methods=['GET', 'POST'])
def api():
    digits = 100
    calculate = False
    value = None
    if request.method == 'POST':
        # check if the post request has the file part
        if 'digits' not in request.form:
            return 'Number of digits was missing'
        else:
            digits = int(request.form['digits'])
            calculate = True
            if digits > 10000:
                return 'Number of digits requested is too high. Try less than 10,000.'

    if request.method == 'GET':
        parm = request.args.get('digits', type=str)
        if parm:
            digits = int(parm)
            if digits > 10000:
                return 'Number of digits requested is too high. Try less than 10,000.'
            calculate = True
    
    value = None
    duration = None
    if calculate:
        print('calculating pi to ', digits)
        start = timer()
        value = calculate_pi(digits)
        end = timer()
        duration = end - start

    return render_template('index.html', digits=digits, value=value, duration=duration)

if __name__ == "__main__":
    http_server = WSGIServer(('', int(os.environ.get('PORT', 8080))), app)
    http_server.serve_forever()
