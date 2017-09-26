'''
Created on 4 May 2017

@author: alex
'''

from flask import Flask
from flask import render_template, redirect, jsonify
from datetime import datetime, timedelta
from flask import request
from icalendar import Calendar
import datetime
from BeautifulSoup import BeautifulSoup
import pytz
import requests
import io
import twitter
from random import randint

from creds import twitter_creds, secret_key

from flask_wtf import Form
from wtforms import StringField, SelectField, IntegerField

utc = pytz.UTC

app = Flask(__name__)
app.config.update(TEMPLATES_AUTO_RELOAD=True)
app.config['SECRET_KEY'] = secret_key

hosts = ["rpi-kitchen",
		"rpi-lounge",
		"rpi-drawing",
		"rpi-pantry-1",
		"rpi-pantry-2"]

lookup = [["all","all"]] + [[x,x] for x in hosts]

class FlashMessage(Form):
	title = StringField('title')
	text = StringField('text')
	length = IntegerField('duration',default=10)
	limit = SelectField('limit to one computer',choices=lookup)
	
class Message(object):
	
	messages = []
	
	def __init__(self,title,body="",length=10,host="all"):
		
		self.id = randint(1,20000)
		self.title = title
		self.body = body
		self.length = length
		self.host = host
		self.time = datetime.datetime.now()
		self.__class__.messages.append(self)
		
	def still_valid(self,host):
		n = datetime.datetime.now()
		d = datetime.timedelta(seconds=self.length)
		time = self.time > (n - d) and self.time < (n + d)
		return self.host in ["all",host] and time
	
	def json(self):
		return {"title":self.title,
				"body":self.body,
				"length":self.length * 1000,
				"id":self.id}
	
	@classmethod
	def valid(cls, host="all"):
		return [x.json() for x in cls.messages if x.still_valid(host)]
		

@app.route('/message/', methods=["GET", "POST"])
def message():
	form = FlashMessage()
	if form.validate_on_submit():
		Message(form.title.data,
				form.text.data,
				form.length.data,
				form.limit.data)
		return redirect("/message/")
	return render_template('send_message.html', form=form)

class error_proof(object):
	
	def __init__(self,func):
		self.func = func
		self.previous_value = None
		
	def __call__(self):
		if self.previous_value:
			try:
				v = self.func()
			except Exception:
				v = self.previous_value
			return v
		else:
			v = self.func()
			self.previous_value = v
			return v

@error_proof
def get_tweets():
	api = twitter.Api(**twitter_creds)
	search = api.GetSearch("#nwspk")
	results = []
	boring_users = ["pwndoor", "nwspk"]
	boring_content = ["RT @nwspk",
					  "@pwndoor"]
	for s in search:
		if s.user.screen_name not in boring_users:
			results.append("@" + s.user.screen_name + ": " + s.text)    
			for b in boring_content:
				if b in s.text:
					results.pop()
					break
	return results[:3]


"""
@app.route('/election/')
def election_redirect():
	return redirect("http://192.168.1.57:8000/election/")
"""

@app.route('/random/')
def random():
	n = randint(0, 2)
	
	host = request.args.get('host')
	
	if n == 0:
		url = "/events/"
	else:
		url = "/"
	
	return redirect(url + "?host={0}".format(host))
	
def local_now():
	return utc.localize(datetime.datetime.now())

@app.route("/")
def screen():
	
	host = request.args.get('host')
	# code for election
	n = datetime.datetime.now()
	#n = datetime.datetime(2017, 6, 8, 20, 30)
	d1 = datetime.datetime(2017, 6, 8, 21, 0)
	delta = (d1 - n).days
	election_hours = (d1 - n).seconds / (60 * 60)
	
	count, members = get_members()
	
	context = {"date":n.strftime("%A %d %B"),
			   "election_days":delta,
			   "election_hours":election_hours,
			   'events':calendar_events(),
			   "members_count":count,
			   "members":members,
			   "tweets":get_tweets(),
			   "host": host}

	return render_template(r'index.html',
					   **context)



@app.route("/flash/")
def flash_message():
	host = request.args.get('host')
	return jsonify(Message.valid(host))

@app.route("/test/")
def test():
	Message("New Message!")
	return jsonify(Message.valid())

@app.route("/events/")
def events():
	
	host = request.args.get('host')
	n = datetime.datetime.now()
	
	d1 = datetime.datetime(2017, 6, 8)
	delta = d1 - n
	context = {"date":n.strftime("%A %d %B"),
			   'events':calendar_with_desc(),
			   "host":host }

	return render_template(r'events.html',
					   **context)    

@app.route("/assign/")
def assign():
	host = request.args.get('host')

	lookup = {"rpi_kitchen":"/random/"}
	
	url = lookup.get(host,"/random/") + "?host={0}".format(host)
	
	return redirect(url)
	


@app.errorhandler(404)
def generic_error_404(e):
	return render_template('error.html'), 404

@app.errorhandler(500)
def generic_error(e):
	return render_template('error.html'), 500

@error_proof
def get_members():
	req = requests.get("http://www.nwspk.com")    
	soup = BeautifulSoup(req.content)
	
	for r in soup.findAll("span", {"class":"membership-progress"}):
		count = r.text.replace("  members", "")
		break
	
	members = []
	for r in soup.findAll("span", {"class":"member-title"}):
		members.append(r.text)
		
	return count, members

	

@error_proof
def calendar_events():
	"""
	get small verson of events for one page summary
	"""
	
	req = requests.get("http://www.nwspk.com/api/events.ics")
	file = io.BytesIO(req.content)
	cal = Calendar.from_ical(file.read())
	n = local_now()
	
	results = []
	for e in cal.walk('vevent'):
		name = e["summary"]
		start = e["dtstart"].dt
		end = e["dtend"].dt
		if end > n and "ration club" not in name.lower():
			row = [start.strftime("%a %d %B") + ": " + unicode(name), start]
			results.append(row)

	results.sort(key=lambda x:x[1])
	results = [x[0] for x in results]

	final = []
	total = 0
	for r in results:
		final.append(r)
		total += len(r)
		if total > 110:
			break

	return final

@error_proof
def calendar_with_desc():
	"""
	get calendar to populate events screens with pages
	"""
	
	req = requests.get("http://www.nwspk.com/api/events.ics")
	file = io.BytesIO(req.content)
	cal = Calendar.from_ical(file.read())
	n = local_now()
	
	results = []
	for e in cal.walk('vevent'):
		entry = {}
		entry["name"] = e["summary"]
		entry["start"] = e["dtstart"].dt
		entry["end"] = e["dtend"].dt
		if "ration club" not in entry["name"].lower():
			if entry["start"].date() == n.date():
				entry["start_nice"] = "Today " + (entry["start"] + timedelta(hours=1)).strftime("%I:%M %p")			
			elif n >= entry["start"] and n < entry["end"]:
				entry["start_nice"] = "Now!"
			else:
				entry["start_nice"] = (entry["start"] + timedelta(hours=1)).strftime("%a %d %B %I:%M %p")
		summary = e["DESCRIPTION"]
		if len(summary) > 300:
			summary = summary[:300] + "..."
		
		entry["desc"] = summary
		if entry["end"] > n:
			results.append(entry)

	results.sort(key=lambda x:x["start"])

	return results[:6]	
		

if __name__ == "__main__":
	#print get_members()
	app.run(host='0.0.0.0')