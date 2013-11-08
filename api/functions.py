#!/usr/bin/env python

# Developed by Yasyf Mohamedali @ HackMIT 2013
# https://github.com/yasyf/PbNotify

import hashlib, datetime, json, calendar, collections, os
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import json_util
import twilio.twiml

client = MongoClient(os.environ['db'])
db = client.hackmit
users = db.users
notifications = db.notifications

def twilio_sms_response(body):
	components = body.split("|")
	if len(components) != 3:
		response = "sms must be in the format of <userid>|<source>|<text>"
	else:
		userid = components[0]
		source = components[1]
		text = components[2]
		
		if check_userid(userid):
			if len(source) > 0 and len(text) > 0:
				response = create_notification(userid, source, text)
			else:
				response = "missing required parameter"
		else:
			response = "invalid userid"
	resp = twilio.twiml.Response()
	resp.message(response)
	return str(resp)
	
def isset_credentials(username, password):
	return (len(username) > 0) and (len(password) > 0)

def validate_credentials(username, password):
	return isset_credentials(username, password) and (users.find({"username": username}).count() == 0)

def check_credentials(username, password):
	return isset_credentials(username, password) and (users.find({"username": username}).count() != 0) and (sha1(password) == users.find({"username": username})[0]["password"])

def get_userid(username):
	return str(users.find({"username": username})[0]["_id"])

def check_userid(userid):
	try:
		return (users.find({"_id": ObjectId(userid)}).count() == 1)
	except Exception:
		return False

def check_notificationid(notificationid):
	return (notifications.find({"_id": ObjectId(notificationid)}).count() == 1)
	
def sha1(text):
	m = hashlib.sha1()
	m.update(text)
	return m.hexdigest()
	
def create_user(username, password):
	return str(users.insert({"username": username, "password": sha1(password)}))
	
def create_notification(userid, source, text):
	return json.dumps({"1": "notificationid", "2": str(notifications.insert({"userid": userid, "time": datetime.datetime.utcnow(), "source": source, "text": text, "delivered": "false"}))})


def get_notification(notificationid, userid):
	obj = notifications.find({"_id": ObjectId(notificationid), "userid": userid})[0]
	obj2 = {"1": "source", "2": obj["source"], "3": "text", "4": obj["text"]}
	return json.dumps(collections.OrderedDict(sorted(obj2.items())))

def get_notifications(userid):
	return notifications.find({"userid": userid}).sort("time", -1)

def get_most_recent_notification(userid):
	if notifications.find({"userid": userid, "delivered": "false"}).count() == 0:
		return json.dumps({"1": "error", "2": "no new messages"})
	notificationid = str(notifications.find({"userid": userid, "delivered": "false"}).sort("time", -1)[0]["_id"])
	return get_notification(notificationid, userid)

def compare_ids(userid, notificationid):
	return (userid == notifications.find({"_id": ObjectId(notificationid)})[0]["userid"])
	
def show_error(text):
	return json.dumps({"1": "error", "2": text})
		
def mark_notification_delivered(userid, delivered):
	if notifications.find({"userid": userid, "delivered": "false"}).count() == 0:
		return json.dumps({"1": "error", "2": "no new messages"})
	if delivered == True:
		status = "true"
	else:
		status = "false"
	notificationid = str(notifications.find({"userid": userid, "delivered": "false"}).sort("time", -1)[0]["_id"])
	notifications.update({"_id": ObjectId(notificationid)}, {"$set": {"delivered": status}})
	return json.dumps({"1": "notificationid", "2": notificationid})

def set_account_token(userid, token):
	users.update({"_id": ObjectId(userid)}, {"$set": {"token": token}})
	return json.dumps({"1": "token", "2": token})

def get_account_token_raw(userid):
	try:
		token = users.find({"_id": ObjectId(userid)})[0]["token"]
		return token
	except KeyError:
		return ""

def get_account_token(userid):
	try:
		token = users.find({"_id": ObjectId(userid)})[0]["token"]
		return json.dumps({"1": "token", "2": token})
	except KeyError:
		return json.dumps({"1": "error", "2": "no token set for this userid"})

def get_account_userid(token):
	try:
		userid = str(users.find({"token": token)[0]["_id"])
		return json.dumps({"1": "userid", "2": userid})
	except KeyError:
		return json.dumps({"1": "error", "2": "no userid found at this token"})

