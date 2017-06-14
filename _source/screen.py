'''
Created on 4 May 2017

@author: alex
'''

from flask import Flask
from flask import render_template, redirect
from datetime import datetime, timedelta
from icalendar import Calendar
import datetime
from BeautifulSoup import BeautifulSoup
import pytz
import requests
import io
import twitter
from random import randint

from creds import twitter_creds

class ErrorProof(object):
	
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

@ErrorProof
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

utc = pytz.UTC

app = Flask(__name__)
app.config.update(TEMPLATES_AUTO_RELOAD=True)

"""
@app.route('/election/')
def election_redirect():
	return redirect("http://192.168.1.57:8000/election/")
"""

@app.route('/random/')
def random():
	n = randint(0, 2)
	
	if n == 0:
		return redirect("/events/")
	return redirect("/")
	
def local_now():
	return utc.localize(datetime.datetime.now())

@app.route("/")
def screen():
	
	# code for election
	n = datetime.datetime.now()
	#n = datetime.datetime(2017, 6, 8, 20, 30)
	d1 = datetime.datetime(2017, 6, 8, 21, 0)
	delta = (d1 - n).days
	election_hours = (d1 - n).seconds / (60 * 60)
	
	context = {"date":n.strftime("%A %d %B"),
			   "election_days":delta,
			   "election_hours":election_hours,
			   'events':calendar_events(),
			   "members":get_members(),
			   "tweets":get_tweets()}

	return render_template(r'index.html',
					   **context)
	
@app.route("/events/")
def events():
	
	n = datetime.datetime.now()
	
	d1 = datetime.datetime(2017, 6, 8)
	delta = d1 - n

	context = {"date":n.strftime("%A %d %B"),
			   'events':calendar_with_desc(), }

	return render_template(r'events.html',
					   **context)    

@ErrorProof
def get_members():
	req = requests.get("http://www.nwspk.com")    
	soup = BeautifulSoup(req.content)
	
	for r in soup.findAll("span", {"class":"membership-progress"}):
		return r.text.replace("  members", "")

@ErrorProof
def calendar_events():
	
	req = requests.get("http://www.nwspk.com/api/events.ics")
	file = io.BytesIO(req.content)
	cal = Calendar.from_ical(file.read())
	n = local_now()
	
	results = []
	for e in cal.walk('vevent'):
		name = e["summary"]
		start = e["dtstart"].dt
		end = e["dtend"].dt
		if end > n:
			row = [start.strftime("%a %d %B") + ": " + unicode(name), start]
			results.append(row)

	results.sort(key=lambda x:x[1])
	results = [x[0] for x in results]

	return results[:4]

@ErrorProof
def calendar_with_desc():
	
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
		if entry["start"].date() == n.date():
			entry["start_nice"] = "Today " + (entry["start"] + timedelta(hours=1)).strftime("%I:%M %p")			
		elif n >= entry["start"] and n < entry["end"]:
			entry["start_nice"] = "Now!"
		else:
			entry["start_nice"] = (entry["start"] + timedelta(hours=1)).strftime("%a %d %B %I:%M %p")
		summary = e["DESCRIPTION"]
		if len(summary) > 370:
			summary = summary[:370] + "..."
		
		entry["desc"] = summary
		if entry["end"] > n:
			results.append(entry)

	results.sort(key=lambda x:x["start"])

	return results[:6]	
		

if __name__ == "__main__":
	app.run(host='0.0.0.0')