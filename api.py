## -*- coding: utf-8 -*-
from urllib2 import urlopen
import urllib2
from os import mkdir
from os import path
import os
import json
from string import zfill
import threading
import telebot
import time
import sys

#ZoneMinder url
zm_url = 'http://zm.loc/zm/' 
chat = 'yourchatid'
min_score = 5
TOKEN = 'yourtoken'
bot = telebot.TeleBot(TOKEN)

def get_from_api():
	print 'get_from_api'
	out_dict = dict()

	url = urlopen(zm_url+'api/events.json').read()
	result = json.loads(url)
	last_page = str(result[u'pagination'][u'pageCount']) #get number of last page
	per_page_count = len(result[u'events']) #number of elements per page
	url = urlopen(zm_url+'api/events.json?page='+last_page).read()
	result = json.loads(url) #get data from last page
	last_event_id =  result[u'events'][-1][u'Event'][u'Id'].encode("utf-8") #last event's id

	try:
		with open('tmp', 'r') as f:
			last_event_id_prev = f.read()

	except (IOError):
		#last_event_id_prev = 0 # uncomment for get ALL events
		last_event_id_prev = last_event_id
		with open('tmp', 'w') as f:
			f.write(last_event_id_prev)

	prev_page = int(last_page) - (int(last_event_id) - int(last_event_id_prev)) / per_page_count

	last_events_id = [] #list of events for event's loop
	if int(last_page) == int(prev_page):
		for i in result[u'events']: #event's loop
			id = i[u'Event'][u'Id'].encode("utf-8")
			if int(id) > int(last_event_id_prev):
				last_events_id.append(id)

	else:
		while int(prev_page) is not int(last_page) + 1:
			# print zm_url+'api/events.json?page='+str(prev_page)
			# prevl_page = int(prev_page) + 1
			url = urlopen(zm_url+'api/events.json?page='+str(prev_page)).read()
			result = json.loads(url)
			for i in result[u'events']: #event's loop
				id = i[u'Event'][u'Id'].encode("utf-8")
				if int(id) > int(last_event_id_prev):
					last_events_id.append(id)
			prev_page = int(prev_page) + 1

	for event in last_events_id: #Now we get data for each event


		url = urlopen(zm_url+'api/events/'+str(event)+'.json').read()

		result = json.loads(url)
		eventpath = result[u'event'][u'Event'][u'BasePath'] #path like "events/1/17/06/01/15/26/12/""
		eventpath = eventpath.replace('\\','').encode("utf-8")
		monitor_name = result[u'event'][u'Monitor'][u'Name'].encode("utf-8")
		try:
			score = result[u'event'][u'Event'][u'TotScore'].encode("utf-8")
		except (IndexError):
			print 'slow score'
			time.sleep(3)
			score = result[u'event'][u'Event'][u'TotScore'].encode("utf-8")
		if int(score) < int(min_score):
			print 'score < 100'
			continue

		alarm_frame_id = [] #we get only alarm frame
		for j in result[u'event'][u'Frame']:
			if j[u'Type'] == u'Alarm':
				alarm_frame_id.append(j[u'FrameId'].encode("utf-8"))
		middle = len(alarm_frame_id) /2 #we get frame from middle of frame list
		try:
			middle_alarm_frame_url = zm_url+eventpath+alarm_frame_id[middle].zfill(5)+'-capture.jpg'
		except (IndexError):
			print 'slow frame'
			time.sleep(3)
			middle_alarm_frame_url = zm_url+eventpath+alarm_frame_id[middle].zfill(5)+'-capture.jpg'
			print middle_alarm_frame_url
		#data for dict
		start_time = result[u'event'][u'Event'][u'StartTime'].encode("utf-8")
		link = zm_url+'index.php?view=event&eid='+event
		out_dict[event] = {'start time':start_time, 'score':score, 'link':link, 'camera':monitor_name}

		if not path.exists(monitor_name):
			mkdir(monitor_name)
		try:
			f = urlopen(middle_alarm_frame_url)
		except (urllib2.HTTPError):
			print middle_alarm_frame_url
			return
		#f = urlopen(middle_alarm_frame_url)
		data = f.read()
		name = event+'.jpg'
		#write image
		with open(path.join(monitor_name,name), "w") as file:
			file.write(data)
		out_dict[event].update({'imagepath':path.join(monitor_name,name)})
		with open('tmp', 'w') as f:
			f.write(event)
		#write dict to json
		# with open(path.join(monitor_name,event+'.json'), "w") as f:
		# 	json.dump(out_dict, f)

	return (out_dict)



def send_to_chat(msg, file=False):
	print msg
	chat_id = chat
	if file:
		photo = open(file, 'rb')
		bot.send_photo(chat_id, photo)
	bot.send_message(chat_id, msg)




def monitoring():
	result = get_from_api()
	threading.Timer(10.0, monitoring).start()
	print 'result'
	print result
	for key in result:
		file = result[key]['imagepath']
		msg = result[key]
		print ("{0}\n{1}\n{2}\n").format('Event Start: '+msg['start time'],'Camera: '+'#'+msg['camera'],msg['link'])
		print msg, 'msg'
		send_to_chat(msg, file)
		os.remove(file)


	exit()


monitoring()
