#!python3

import argparse, m3u8, requests, ssl, urllib3, os
from time import sleep

parser = argparse.ArgumentParser()
parser.add_argument('url', help='m3u8 file URL')
parser.add_argument('filename', help='target file')
args = parser.parse_args()

urllib3.disable_warnings()
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

tempdirname = '{}.tempdir'.format(args.filename)
if os.path.isdir(tempdirname):
	print('Temp dir exists, resuming download')
else:
	os.mkdir(tempdirname)

segmentfiles = []
base_uri = args.url[:args.url.rfind("/")+1]
m3u8_response = requests.get(args.url, verify=False)
m3u8_obj = m3u8.loads(m3u8_response.text)
for segment in m3u8_obj.segments:
	segmentfilename = '{}/{}'.format(tempdirname, segment.uri[segment.uri.rfind('/')+1:])
	segmentfiles.append(segmentfilename)
	if os.path.isfile(segmentfilename):
		# print('skipping', segmentfilename)
		continue
	print(segment.uri)
	retries = 3
	while retries:
		try:
			seg_response = requests.get(('' if segment.uri[:4]=='http' else base_uri)  + segment.uri, verify=False)
			with open(segmentfilename, 'wb') as sf:
				sf.write(seg_response.content)
			break
		except ConnectionResetError:
			retries -= 1
			print('\tConnectionResetError exception, retry', 3-retries)
			sleep(2)
	if retries == 0:
		print('Failed too many times, finishing')
		exit(1)

print('Assembling {} files...'.format(len(segmentfiles)))
with open(args.filename, 'wb') as f:
	for sfname in segmentfiles:
		with open(sfname, 'rb') as sf:
			f.write(sf.read())
			print('.', end='', flush=True)
print('')
print('Done', args.filename)
