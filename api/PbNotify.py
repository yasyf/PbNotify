#!/usr/bin/env python

# Developed by Yasyf Mohamedali @ HackMIT 2013
# https://github.com/yasyf/PbNotify

from flask import Flask, Response, session, redirect, url_for, escape, request, render_template
from functions import *

app = Flask(__name__)
app.secret_key = os.environ['sk']

	
@app.route('/')
def index():
	if 'userid' in session:
		return render_template('index.html', notifications=get_notifications(session["userid"]), token=get_account_token_raw(session["userid"]))
	else:
		return redirect(url_for('login', error="Please login or register below."))

@app.route('/sms')
def sms_response():
	return twilio_sms_response(request.values.get('Body', ''))

@app.route('/logout')
def logout():
	session.pop('userid')
	return redirect(url_for('index'))

@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method == 'POST':
		username = request.form.get('username','')
		password = request.form.get('password','')
		if check_credentials(username,password):
			session["userid"] = get_userid(username)
			return redirect(url_for('index'))
		elif validate_credentials(username,password):
			session["userid"] = create_user(username,password)
			return redirect(url_for('index'))
		else:
			return render_template('login.html',error="Your credentials were invalid.")
	else:
		if 'userid' in session:
			return redirect(url_for('index'))
		else:
			return render_template('login.html',error=request.args.get('error', ''))

@app.route('/api/notification/create/<userid>/<source>/<text>', methods=['POST', 'GET'])
def new_notification(userid, source, text):
	if check_userid(userid):
		if len(source) > 0 and len(text) > 0:
			return Response(response=create_notification(userid, source, text), status=200, mimetype="application/json")
		else:
			error = "missing required parameter"
	else:
		error = "invalid userid"
	return Response(response=show_error(error), status=200, mimetype="application/json")

@app.route('/api/notification/get/<userid>', methods=['POST', 'GET'])
def retreive_most_recent_notification(userid):
	if check_userid(userid):
		resp = get_most_recent_notification(userid)
		return Response(response=resp, status=200, mimetype="application/json")
	else:
		return Response(response=show_error("invalid userid"), status=200, mimetype="application/json")

@app.route('/api/notification/get/<userid>/<notificationid>', methods=['POST', 'GET'])
def retreive_notification(userid, notificationid):
	if check_userid(userid) and check_notificationid(notificationid) and compare_ids(userid, notificationid):
		return Response(response=get_notification(notificationid, userid), status=200, mimetype="application/json")
	else:
		return Response(response=show_error("invalid notificationid for this userid"), status=200, mimetype="application/json")

@app.route('/api/notification/delivered/<userid>', methods=['POST', 'GET'])
def notification_delivered(userid):
	if check_userid(userid):
		return Response(response=mark_notification_delivered(userid, True), status=200, mimetype="application/json")
	else:
		return Response(response=show_error("invalid userid"), status=200, mimetype="application/json")

@app.route('/api/account/token/<userid>/<token>', methods=['POST', 'GET'])
def set_account_token_call(userid, token):
	if check_userid(userid):
		return Response(response=set_account_token(userid, token), status=200, mimetype="application/json")
	else:
		return Response(response=show_error("invalid userid"), status=200, mimetype="application/json")

@app.route('/api/account/token/<userid>', methods=['POST', 'GET'])
def get_account_token_call(userid):
	if check_userid(userid):
		return Response(response=get_account_token(userid), status=200, mimetype="application/json")
	else:
		return Response(response=show_error("invalid userid"), status=200, mimetype="application/json")

@app.route('/api/account/userid/<token>', methods=['POST', 'GET'])
def get_account_userid_call(token):
	return Response(response=get_account_userid(token), status=200, mimetype="application/json")

	
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080,debug=True)