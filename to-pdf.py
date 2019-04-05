import os
import shutil
import requests
import tempfile
import urllib.request
import json
import sys

from gevent.pywsgi import WSGIServer
from flask import Flask, after_this_request, render_template, request, send_file
from subprocess import call

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = set(['doc', 'docx', 'xls', 'xlsx'])

app = Flask(__name__)


# Convert using Libre Office
def convert_file(output_dir, input_file):
    call('libreoffice --headless --convert-to pdf --outdir %s %s ' %
         (output_dir, input_file), shell=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def api():
    work_dir = tempfile.TemporaryDirectory()
    file_name = 'document'
    input_file_path = os.path.join(work_dir.name, file_name)
    # Libreoffice is creating files with the same name but .pdf extension
    output_file_path = os.path.join(work_dir.name, file_name + '.pdf')
    print('incoming request.', file=sys.stdout)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return 'No file provided'
        file = request.files['file']
        if file.filename == '':
            return 'No file provided'
        if file and allowed_file(file.filename):
            file.save(input_file_path)

    if request.method == 'GET':
        url = request.args.get('url', type=str)
        if not url:
            service_name=detect_service()
            return render_template('index.html', service=service_name)
        # Download from URL
        response = requests.get(url, stream=True)
        with open(input_file_path, 'wb') as file:
            shutil.copyfileobj(response.raw, file)
        del response

    convert_file(work_dir.name, input_file_path)

    @after_this_request
    def cleanup(response):
        work_dir.cleanup()
        return response
 
    return send_file(output_file_path, mimetype='application/pdf')



# Detect if we're running on Cloud Run, Cloud Run on GKE, or Knative
@app.route('/metadata', methods=['GET'])
def detect_service():
    url = 'http://metadata.google.internal/computeMetadata/v1/instance/'
    res = response(url)
    return res
    if res:
        print('got response!', res, file=sys.stdout)
        data = json.loads(res)
        print('parsed json!', file=sys.stdout)
        counter = 0
        for item in data:
            counter += 1
            print('found item in data', counter, file=sys.stdout)
        print('counter value ', counter, file=sys.stdout)
        if counter > 2:
            return 'Cloud Run on GKE'
        if counter != 0:
            return 'Cloud Run'
    print('no data found', file=sys.stdout)
    return 'IBM Cloud with Knative'

def response(url):
    try:
        response = urllib.request.urlopen(url)
        return response.read()
    except urllib.error.URLError as e:        
        return e


if __name__ == "__main__":
    print('PDF service has started up.', file=sys.stdout)
    http_server = WSGIServer(('', int(os.environ.get('PORT', 8080))), app)
    http_server.serve_forever()
