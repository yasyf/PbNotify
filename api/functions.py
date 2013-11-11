#!/usr/bin/env python

# Developed by Yasyf Mohamedali @ HackMIT 2013
# https://github.com/yasyf/PbNotify

import hashlib, datetime, json, calendar, collections, os, time
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import json_util
from datetime import timedelta
from flask import make_response, request, current_app, render_template, redirect, url_for, session
from functools import update_wrapper
import twilio.twiml
import stripe

client = MongoClient(os.environ['db'])
db = client.hackmit
users = db.users
notifications = db.notifications

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

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
	
def create_user(username, password, stripe_cust):
	return str(users.insert({"username": username, "password": password, "stripe_cust": stripe_cust}))
	
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

def clear_history(userid):
	count = notifications.find({"userid": userid, "delivered": "true"}).count()
	notifications.remove({"userid": userid, "delivered": "true"})
	return json.dumps({"1": "notifications", "2": count})

def set_account_token(userid, token):
	users.update({"_id": ObjectId(userid)}, {"$set": {"token": token}})
	return json.dumps({"1": "token", "2": token})

def get_account_token_raw(userid):
	try:
		token = users.find({"_id": ObjectId(userid)})[0]["token"]
		return token
	except Exception:
		return "none"

def get_account_token(userid):
	try:
		token = users.find({"_id": ObjectId(userid)})[0]["token"]
		return json.dumps({"1": "token", "2": token})
	except Exception:
		return json.dumps({"1": "error", "2": "no token set for this userid"})

def gen_promo():
	return "PbNotifyPromo-"+sha1(time.strftime("%d%m%Y"))

def validate_promo(promo):
	if validate_promo_raw(promo) == True:
		return json.dumps({"valid": "true"})
	else:
		return json.dumps({"valid": "false"})

def validate_promo_raw(promo):
	#PbNotifyPromo-sha1({DD}{MM}{YYYY})
	if promo == "PbNotifyPromo-"+sha1(time.strftime("%d%m%Y")):
		return True
	else:
		return False

def get_account_userid(token):
	try:
		userid = str(users.find({"token": token})[0]["_id"])
		return json.dumps({"1": "userid", "2": userid})
	except Exception:
		return json.dumps({"1": "error", "2": "no userid found at this token"})

def stripe_post_login():
	stripe.api_key = os.environ['stripe_sk']
	token = request.form.get('stripeToken','')
	try:
		stripe_cust = stripe.Customer.create(card=token, plan="PBNOTIFYFT", description="PbNotify: " + session["username"])
		session["userid"] = create_user(session["username"], session["password"], stripe_cust.id)
		stripe_cust.description = "PbNotify: %s (%s)" % (session["userid"], session["username"])
		session.pop('username')
		session.pop('password')
		return redirect(url_for('index'))
	except stripe.CardError, e:
		# The card has been declined
		return render_template('stripe_login.html',error=e)
	except Exception:
		return redirect(url_for('index'))

