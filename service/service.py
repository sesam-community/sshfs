from flask import Flask, request, Response
import os
import logger
import json
from paramiko import SSHClient, AutoAddPolicy

app = Flask(__name__)

logger = logger.Logger('sshfs-proxy')

hostname=os.environ['HOSTNAME']
username=os.environ['USERNAME']
password=os.environ['PASSWORD']
buffer_size=os.environ.get("BUFFER_SIZE", 1024)

class SshSession:
    def __init__(self):
        client = SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(AutoAddPolicy())
        logger.info("Logging into %s" % hostname)
        try:
            client.connect(hostname=hostname, username=username, password=password)
        except Exception as e:
            logger.info("could not connect to " + hostname + ":  %s" % e)
            raise Exception("Problem connecting: '%s'" % e)
        self._connection = client
        logger.info("Opened connection")

    def read(self, path):
        stdin, stdout, stderr = self._connection.exec_command('cat ' + path)
        return stdout

    def is_folder(self, path):
        return self._connection.exec_command('if [ -d ' + path + ' ] ; then echo true; else echo false; fi')[1].readlines()[0].replace('\n', '') == "true"

    def is_file(self, path):
        return self._connection.exec_command('if [ -f ' + path + ' ] ; then echo true; else echo false; fi')[1].readlines()[0].replace('\n', '') == "true"

    def get_mime_type(self, path):
        return self._connection.exec_command('file -b --mime-type ' + path)[1].readlines()[0].replace('\n', '')

    def get_filenames(self, path):
        filenames = []
        stdin, stdout, stderr = self._connection.exec_command('ls ' + path)
        for out in stdout.readlines():
            filenames.append(out.replace('\n', ''))
        return filenames

    def write(self, path, stream):
        dir = path.split('/')
        p = ""
        for element in dir:
            if not element == dir[-1]:
                p = p + element + "/"
        self._connection.exec_command('if [ -f '  + path + ' ]; then echo \"' + stream.decode() + '\" >> ' + path + ' ; else mkdir -p ' + p + ' ; echo \"'+ stream.decode() + '\" >> ' + path + ' ; fi')

    def close(self):
        self._connection.close()
        logger.info("Closed connection")


def fix_path(request, path):
    is_relative = request.args.get('relative', False)
    if is_relative:
        return path
    else:
        return '/' + path


@app.route("/<path:path>", methods=["GET"])
def get(path):
    path = fix_path(request, path)
    session = SshSession()
    if session.is_folder(path):
        filenames = session.get_filenames(path)
        files = [{
            "_id": filename,
            "url": request.url_root + filename
        } for filename in filenames]
        return Response(response=json.dumps(files), mimetype='application/json')
    elif session.is_file(path):
        mime_type = session.get_mime_type(path)
        stream = session.read(path)

        def generate():
            while True:
                data = stream.read(buffer_size)
                if not data:
                    break
                yield data
            session.close()
        return Response(response=generate(), mimetype=mime_type)
    else:
        return Response(response="No such file or directory '%s'" % path, status=404)


@app.route('/<path:path>', methods=["POST"])
def post(path):
    path = fix_path(request, path)
    stream = request.stream
    session = SshSession()
    session.write(path, stream)
    session.close()
    return Response(response="Great Success!")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('port',5000))
