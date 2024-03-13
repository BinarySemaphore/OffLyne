import os
import time
import json

from django.http import HttpResponse


def request_logger(request):
    filename = "{}.log".format(time.strftime("%Y_%m_%d"))
    timestamp = time.strftime("%H:%M:%S.") + str(time.time()).split('.')[1][:3]
    block = "{} {} '{}' '{}'\n".format(timestamp, request.method, request.get_host(), request.path)
    block += "{}\n".format(request.session)
    block += "Body:\n{}\n".format(request.body)
    block += "Headers:\n{}\n".format(request.headers)
    block += "Cookies:\n{}\n".format(request.COOKIES)
    
    with open(os.path.join('captures', filename), 'a') as f:
        f.write(block + '-' * 80 + '\n\n')
    
    return HttpResponse("")