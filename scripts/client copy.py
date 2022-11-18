#!/usr/bin/env python3

import cv2
from time import sleep
import struct
import redis
import numpy as np
import json
from sshtunnel import SSHTunnelForwarder

ESC = 27
LEFT_SHIFT = 225

# get data from redis server and decode JPEG data
def fromRedis(hRedis,topic):
	"""Retrieve Numpy array from Redis key 'topic'"""
	encoded = hRedis.get(topic)
	h, w = struct.unpack('>II',encoded[:8])		# unpack

	# make numpy array
	a = np.frombuffer(encoded, dtype=np.uint8, offset=8)

	# decode jpeg to opencv image
	decimg = cv2.imdecode(a, flags=cv2.IMREAD_UNCHANGED).reshape(h,w,3)

	return decimg

# Main Function
if __name__ == '__main__':
	# Redis connection
	ssht = SSHTunnelForwarder(
        	("163.143.132.153", 22),
        	ssh_host_key=None,
        	ssh_username="uavdata",
        	ssh_password="0158423046",
        	ssh_pkey=None,
        	remote_bind_address=("localhost", 6379))
	ssht.start()
	r = redis.Redis(host='localhost', port=ssht.local_bind_port, db=0)
	r.set('command', '')
	cmd = ''

	# loop until you press Ctrl+c
	try:
		while True:
			# Topic name of OpenCV image is "image"
			img = fromRedis(r,'image')

			# Topic name of Tello Status is "state"
			json_state = r.get('state')
			dict_state = json.loads( json_state )	# convert to Dictionary
			print( 'Battery:%d '%(dict_state['bat']) )

			# show OpenCV image
			cv2.imshow('Image from Redis', img)

			# wait key-input 1ms on OpenCV window
			key = cv2.waitKey(1)
			if key == ESC:				# exit
				break
			elif key == LEFT_SHIFT:
				r.set('command', 'stop')
			elif key == ord('m'):		# arm throttle
				r.set('command','arm')	# r.set([Topic],[Payload]) Topic is "command". Payload is SDK command.
			elif key == ord('n'):		# disarmed
				r.set('command', 'disarmed')
			elif key == ord('t'):		# takeoff
				r.set('command','takeoff')
			elif key == ord('l'):		# land
				r.set('command','land')
			elif key == ord('w'):		# forward
				r.set('command','forward')
			elif key == ord('s'):		# back
				r.set('command','back')
			elif key == ord('a'):		# move left
				r.set('command','left')
			elif key == ord('d'):		# move right
				r.set('command','right')
			elif key == ord('q'):		# turn left
				r.set('command','rotate_left')
			elif key == ord('e'):		# turn right
				r.set('command','rotate_right')
			elif key == ord('r'):		# move up
				r.set('command','up')
			elif key == ord('f'):		# move down
				r.set('command','down')


	except( KeyboardInterrupt, SystemExit):    # if Ctrl+c is pressed, quit program.
		print( "Detect SIGINT." )
