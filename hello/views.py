from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from .models import Greeting
import json, random, requests
import os
import psycopg2
import urlparse

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

cur = conn.cursor()

selectGreetings = """SELECT message_text
					FROM greetings
					LEFT JOIN races on races.id=races_id::integer
					WHERE races.name=%(desired_race)s
					ORDER BY RANDOM()
					LIMIT 1"""
selectFarewells = """SELECT message_text
					FROM farewells
					LEFT JOIN races on races.id=races_id::integer
					WHERE races.name=%(desired_race)s
					ORDER BY RANDOM()
					LIMIT 1"""
checkRace = "SELECT id FROM races WHERE name=%(race_name)s"
selectAllRaces = "SELECT name FROM races"
selectRandomRace = "SELECT name FROM races ORDER BY RANDOM() LIMIT 1"

# Create your views here.
def index(request):
	if request.method == 'GET':
		print "Order up!"
		print request.GET
		inputs = dict(request.GET)

		if 'token' in inputs and inputs['token'][0] == OS.environ["APPBACKR_SLACK_TOKEN"]:

			if 'text' in inputs and inputs['text'] != []:

				## get list of all given command words
				text = inputs['text'][0].split(" ")

				## first should be my main command
				greeting_or_farewell = text[0].lower()
				
				## second is optional, specifies race
				if len(text) > 1:
					if text[1].lower() == "night" and text[2].lower() == "elf":
						desired_race = "night elf"
					elif text[1].lower() == "blood" and text[2].lower() == "elf":
						desired_race = "blood elf"
					else:
						desired_race = text[1].lower()
						cur.execute(checkRace, {'race_name':desired_race})
						race_id = cur.fetchone()
						if race_id is None:
							## return an unknown race error
							cur.execute(selectAllRaces,)
							races = cur.fetchall()
							races_list = [str(race[0])for race in races]
							return JsonResponse({"text":"Sorry friend, afraid I've never seen specimen of the %(desired_race)s species round these parts.\nWorld of Warcraft races available for you to choose from are: %(races)s"%{"desired_race":desired_race, "races":races_list}})
						else:
							race_id = race_id[0]
				else:
					cur.execute(selectRandomRace,)
					desired_race = cur.fetchone()[0]


				## check first greeting or farewell or unknown
				if greeting_or_farewell == "greeting":
					cur.execute(selectGreetings, {'desired_race':desired_race})
					wow_message = cur.fetchone()
					if wow_message is not None:
						wow_message = wow_message[0]
						requests.post(inputs['response_url'][0], data=json.dumps({"text":"Master @%(username)s says: %(wow_message)s"%{'username':inputs['user_name'][0], 'wow_message':wow_message}, "response_type":"in_channel"}))
						return HttpResponse(status=201)
					else:
						return JsonResponse({"text":"I'm ever so sorry Master @%(username)s.  It appears my tomes have gotten mixed up.  Please query my wisdom later. :crystal_ball:"%{'username':inputs['user_name'][0]}})

				elif greeting_or_farewell == "farewell":
					cur.execute(selectFarewells, {'desired_race':desired_race})
					wow_message = cur.fetchone()
					if wow_message is not None:
						wow_message = wow_message[0]
						requests.post(inputs['response_url'][0], data=json.dumps({"text":"Master @%(username)s says: %(wow_message)s"%{'username':inputs['user_name'][0], 'wow_message':wow_message}, "response_type":"in_channel"}))
						return HttpResponse(status=201)
					else:
						return JsonResponse({"text":"I'm ever so sorry Master @%(username)s.  It appears my tomes have gotten mixed up.  Please query my wisdom later. :crystal_ball:"%{'username':inputs['user_name'][0]}})

				elif greeting_or_farewell == "":
					return JsonResponse({"text":"Try either 'greeting' or 'farewell' and I'll return a random World of Warcraft quote of that type. :crossed_swords:"})

				elif greeting_or_farewell == "races":
					cur.execute(selectAllRaces,)
					races = cur.fetchall()
					if races == []:
						return JsonResponse({"text":"I'm ever so sorry Master @%(username)s.  It appears my tomes have gotten mixed up.  Please query my wisdom later. :crystal_ball:"%{'username':inputs['user_name'][0]}})
					else:
						races_list = [str(race[0]) for race in races]
						return JsonResponse({"text":"World of Warcraft races available for you to choose from are: %(races)s  (Make your selection after 'greeting' or 'farewell')"%{"races":races_list}})

				else:
					return JsonResponse({"text":"Sorry friend, afraid I'm not attuned to \"%(input_text)s\" in these parts.  You'll have better luck with either 'greeting' or 'farewell'. :crossed_swords:."%{'input_text': text[0]}})






def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})

