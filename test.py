from hyper import HTTPConnection

import logging

log = logging.getLogger('hyper')
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

print("First hyper request")
conn = HTTPConnection('http2bin.org:443')
conn.request('GET', '/get')
resp = conn.get_response()
conn.close()
print(resp.read())

#print("Second hyper request")
#conn.request('GET', '/ip')
#resp = conn.get_response()
#print(resp.read())

#print("Third hyper request")
#conn.request('GET', '/headers')
#resp = conn.get_response()
#print(resp.read())

log.debug('End')