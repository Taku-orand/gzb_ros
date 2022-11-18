#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import tello		# import tello.py
import time		# for time.sleep() function
import cv2			# OpenCV
import struct
import redis
import numpy as np
import json
from sshtunnel import SSHTunnelForwarder
import rospy
import sys
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge, CvBridgeError

def writeRedis(r,a,n):
	"""Store given Numpy array 'a' in Redis under key 'n'"""
	h, w = a.shape[:2]
	shape = struct.pack('>II',h,w)

	encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
	result, encimg = cv2.imencode('.jpg', a, encode_param)

	encoded = shape + encimg.tobytes()

	# Store encoded data in Redis
	r.set(n,encoded)
	return

input_image = None
bridge = None
# Main Function
def main():
	global bridge
	global input_image

	# Rospy
	node_name = "Camera_image"
	rospy.init_node(node_name,anonymous=True)
	rospy.on_shutdown(cleanup)
	bridge = CvBridge()
	rospy.Subscriber("/image_raw", Image, image_callback, queue_size=1)


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
	#r = redis.Redis(host='', port=6379, db=0)

	# make instance as "drone" using Tello class
	#drone = tello.Tello( command_timeout=.01 )

	current_time = time.time()	# current time
	pre_time = current_time		# for sending 'command' each 5 seconds

	time.sleep(0.5)		# wait for stable connection

	# make new OpenCV window for Tarckbar
	cv2.namedWindow("OpenCV Window")

	# empty function for Trackbar callback
	def nothing(x):
		pass

	# make Trackbar
	cv2.createTrackbar("Battery", "OpenCV Window", 50, 100, nothing)
	cv2.createTrackbar("Tof", "OpenCV Window", 50, 1000, nothing)
	cv2.createTrackbar("h", "OpenCV Window", 50, 1000, nothing)

	# Message Initialize
	#r.set('command', '')
	#r.set('response', '')
	#res = ""
	# loop until Ctrl+c pressed
	try:
		while True:
			# cmd = r.get('command')

			# if cmd != None:
			# 	cmd = cmd.decode()
			# 	if len(cmd) != 0:
			# 		print(cmd)
			# 		r.set('command', '')
			# 		res = drone.send_command(cmd)

			# (A)get image
			# frame = drone.read()	# get 1 frame
			# if frame is None or frame.size == 0:		# correct data?
				# continue
			# Subscribe "image_raw"
			# rospy.Subscriber("/image_raw", Image, image_callback, queue_size=1)
			

			if input_image is None or input_image.size == 0:
				continue

			# (B)processing
			#image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)		# change OpenCV color plane
			# image = frame
			#small_image = cv2.resize(image, dsize=(320,240) )	# change 1/3 size
			#small_image = cv2.resize(image, dsize=(480,360) )	# change 1/2 size

			# (X)show window
			cv2.imshow('OpenCV Window', input_image)

			# show tello info
			# if drone.state is not None:
			# 	cv2.setTrackbarPos("Battery", "OpenCV Window", drone.state["bat"])
			# 	cv2.setTrackbarPos("Tof", "OpenCV Window", drone.state["tof"])
			# 	cv2.setTrackbarPos("h", "OpenCV Window", drone.state["h"])

			# (Y)key input
			key = cv2.waitKey(1)
			if key == 27:					# 27 = ESC key), exit program
				break
			# elif key == ord('m'):				# motor start
			# 	res = drone.send_command('motoron')
			# elif key == ord('o'):				# motor stop
			# 	res = drone.send_command('motoroff')
			# elif key == ord('t'):
			# 	res = drone.takeoff()				# takeoff
			# elif key == ord('l'):
			# 	res = drone.land()					# land
			# elif key == ord('w'):
			# 	res = drone.move_forward(0.3)		# move forward
			# elif key == ord('s'):
			# 	res = drone.move_backward(0.3)		# move back
			# elif key == ord('a'):
			# 	res = drone.move_left(0.3)			# move left
			# elif key == ord('d'):
			# 	res = drone.move_right(0.3)			# move right
			# elif key == ord('q'):
			# 	res = drone.rotate_ccw(20)			# turn left
			# elif key == ord('e'):
			# 	res = drone.rotate_cw(20)			# turn right
			# elif key == ord('r'):
			# 	res = drone.move_up(0.3)			# move up
			# elif key == ord('f'):
			# 	res = drone.move_down(0.3)			# move down

			# (Y) write data to Redis
			writeRedis(r, input_image, 'image')	# write image

			# write response to Redis
			# if(res != '' and res is not None):
			# 	print(res + ":" + cmd)
			# 	r.set('response', res + ":" + cmd)
			# res = ""
			# write tello info and show
			# if drone.state is not None:
			# 	json_state = json.dumps( drone.state )
			# 	#print(json_state)
			# 	r.set('state', json_state)

			# # (Z)send 'command' each 5 seconds
			# current_time = time.time()	# current time
			# if current_time - pre_time > 5.0 :	# 5 seconds passed?
			# 	drone.send_command('command')	# send 'command'
			# 	pre_time = current_time			# update previous time
			# rospy.spin()




	except( KeyboardInterrupt, SystemExit):    # detect Ctrl+c pressed
		print( "detect SIGINT." )

	# delete tello class
	# del drone


# def image_subscribe():
# 	node_name = "Camera_image"
# 	rospy.init_node(node_name)
# 	rospy.on_shutdown(cleanup)
# 	bridge = CvBridge()
# 	rospy.Subscriber("/image_raw", Image, image_callback, queue_size=1)

def image_callback(ros_image):
	global bridge
	global input_image
	try:
		input_image = bridge.imgmsg_to_cv2(ros_image, "bgr8")
	except CvBridgeError, e:
		print e
	#cv2.imshow("Camera_image", input_image)
	#writeRedis(r,input_image,'image')
	
def cleanup():
	cv2.destroyAllWindows()



if __name__ == "__main__":
	main()    # call Main Function
