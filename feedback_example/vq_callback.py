import re
import subprocess

command = "sipping.py -d {ip} -p {port} -r templates/vq_feedback.xml -v"

def vq_callback(sock, request):
    body = request.split('\n')
    data = {}
    
    for line in body:
        data[line.split(':')[0]] = ':'.join(line.split(':')[1:]).strip()
    
    if data.has_key('QualityEst'):
        moslq_re = re.compile('.*MOSLQ=([0-5]\.[0-9]).*')
        m = moslq_re.match(data['QualityEst'])
        if m:
            moslq = float(m.group(1))
        else:
            moslq = None

        moscq_re = re.compile('.*MOSCQ=([0-5]\.[0-9]).*')
        m = moscq_re.match(data['QualityEst'])
        if m:
            moscq = float(m.group(1))
        else
            moscq = None

        if moscq < 4 or moslq < 4:
            subprocess.Popen()
