from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
import json, random, requests, os, psycopg2, urlparse

## appbackr Endorsement URL [requires package_name & api_key & auth_token]
endorsementUrl = "https://index.appbackr.com/v1/endorsements"
appbackrApiKey = "20fe813188a344f9a29fd22d69f789d9"
appbackrAuthToken = "f70dfa1917c6b3e3e6fb2807e2b65ca5"

## Uber URLs
uberStart = "https://api.uber.com"
timeCheck = "/v1/estimates/time"
surgeCheck = "/v1/estimates/price"
uber_server_token = os.environ["UBER_SERVER_TOKEN"]

## GCal Auths
GCalClientId = os.environ["GCAL_CLIENT_ID"]
GCalClientSecret = os.environ["GCAL_CLIENT_SECRET"]

## connect to appbackr's database
urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["APPBACKR_DB_URL"])
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
cur = conn.cursor()

# Create your views here.
def index(request):

	## get the inputs
	if request.method == 'GET':
		print "GET order up!"
		print request.GET
		inputs = dict(request.GET)
	elif request.method == 'POST':
		print "POST order up!"
		print request.POST
		inputs = dict(request.POST)

	## process
	if 'text' in inputs and inputs['text'] != []:

		## get list of all given command words
		text = inputs['text'][0].split(" ")

		## get response URL
		responseUrl = inputs['response_url'][0]

		## first should be my main command
		thyBidding = text[0].lower()

		if thyBidding == 'help':

			print "They want help."
			return JsonResponse({"text":"Try 'endorsement' followed by an Android ID for a fun fact about that app. :gift:"})

		elif thyBidding == 'endorsement':

			print "They want an endorsement."

			try:
				packageName = text[1]
			except:
				## if this fails it should be because I wasn't given a second text param, i.e. not given a package name
				return JsonResponse({"text":"Sorry, but for me to return you an endorsement, I'll need to know what app you'd like to learn about.\nPlease provide me an Android ID (aka Package Name) like this `/surf endorsement com.Slack`. :calling:"})

			print "Calling Endorsement URL for package_name:",packageName
			endorsementResponse = requests.get(endorsementUrl, params={'package_name':packageName, 'api_key':appbackrApiKey, 'auth_token': appbackrAuthToken})
			print "endorsementResponse status code:",endorsementResponse.status_code
			print "endorsementResponse json:",endorsementResponse.json()

			endorsementData = endorsementResponse.json()

			if endorsementResponse.status_code == 200 and 'response' in endorsementData and 'error' not in endorsementData['response']:

				if 'chosen_key' in endorsementData['response']['endorsement']:

					chosen_key = endorsementData['response']['endorsement']['chosen_key']
					reason = endorsementData['response']['endorsement']['reason']

					print "chosen_key:", chosen_key
					print "reason:", reason

					chosen_name = endorsementData['response']['endorsement'][chosen_key]['name']
					chosen_icon_url = endorsementData['response']['endorsement'][chosen_key]['icon_url']

					app_title = endorsementData['response']['app_details']['title']
					app_icon = endorsementData['response']['app_details']['icon_url']
					app_link = "https://index.appbackr.com/apps/"+packageName

					requests.post(responseUrl,
						data=json.dumps({"text":"Here's your current endorsement for %s:"%app_title,
										"response_type":"in_channel",
										"attachments": [{"author_name":app_title,
														"author_link":app_link,
														"author_icon":app_icon,
														"text":"Because "+reason.lower(),
														"title":"Relevant for: "+chosen_name,
														"thumb_url":chosen_icon_url,
														"footer_icon":"https://lh3.googleusercontent.com/HN6oUA-upH3oPTvP95JQX_Yr9QeCkFnUlEn0U2XgoV9fZSOLldad1eIWln6FR1PEQ20=w196",
														"footer":"Brought to you by your friends at Surf!"
														}]
										}))
					return HttpResponse(status=201)

			else:
				return JsonResponse({"text":"I'm ever so sorry, I seem to have encountered an error.  Please try again with a different Android ID, or with '%s' later on. :disappointed:"%packageName})

		elif thyBidding == 'app':

			## start this with just venue types, and matching any relevant SmartCards

			print "They want an app for a Venue Type."

			return JsonResponse({"text":"Sorry friend, this will be an awesome feature, I promise you.  But I'm not quite ready yet.  Thanks for thinking of me. ::kissing_heart::"})

		elif thyBidding == 'uber':

			## starting this out with just lat, lng

			print "They want the current Uber stuff."

			if len(text) > 2:
				try:
					lat = float(text[1])
					lng = float(text[2])
				except ValueError:
					print "Invalid lat or lng given."
					return JsonResponse({"text":"Sorry friend, looks like the latitude or longitude you provided me is invalid: \"%(input_text)s\" yet.  Try 'uber {lat} {lng}' for a better result. :car:"%{'input_text': text}})
			else:
				print "Invalid lat or lng given."
				return JsonResponse({"text":"Sorry friend, looks like the latitude or longitude you provided me is invalid: \"%(input_text)s\" yet.  Try 'uber {lat} {lng}' for a better result. :car:"%{'input_text': text}})

			#check for Car Availability
			params = {'start_latitude':lat, 'start_longitude':lng, 'server_token':uber_server_token}
			response = requests.get(uberStart+timeCheck, params=params)
			rateLimitRemain = int(response.headers['x-rate-limit-remaining'])
			print "Uber calls remaining:",rateLimitRemain

			if rateLimitRemain > 1:

				# check for Surge Pricing
				params = {'start_latitude':lat, 'start_longitude':lng, 'end_latitude':lat+0.1, 'end_longitude':lng+0.1, 'server_token':uber_server_token}
				secondResponse = requests.get(uberStart+surgeCheck, params=params)
				rateLimitRemain = int(response.headers['x-rate-limit-remaining'])
				print "Uber calls remaining now (after second call):",rateLimitRemain

				secondUberData = secondResponse.json()
				print secondUberData

			uberData = response.json()
			display_name = 'uberX'
			seconds = None
			surgeMultiplier = None

			print "Uber Data JSON:",uberData

			if response.status_code == 200:
				for product in uberData['times']:

					if product['display_name'] == 'uberX':

						print product

						#display_name == product['display_name']
						seconds = product['estimate']
						print "display_name:",display_name
						print "seconds:",seconds

			if secondResponse.status_code == 200:
				for product in secondUberData['prices']:

					if product['display_name'] == 'uberX':

						print "product:",product

						surgeMultiplier = product['surge_multiplier']
						print "surgeMultiplier:",surgeMultiplier

			if seconds is not None and surgeMultiplier is not None:

				print 'Wait time for %s: %s secs.'%(display_name, seconds)

				m, s, h = 0, 0, 0
				m, s = divmod(seconds, 60)
				h, m = divmod(m, 60)

				requests.post(responseUrl,
					data=json.dumps({"text":"Here's the current Uber information for (%s,%s):"%(lat,lng),
									"response_type":"in_channel",
									"attachments": [{"author_name":"Uber",
													"author_link":"https://index.appbackr.com/apps/com.ubercab",
													"author_icon":"https://lh3.googleusercontent.com/aMoTzec746RIY9GFOKMjipqBShsKos_KxeDtS59tRp4-ePCpGqW2bS-ySyUEL6q3gkA=w196",
													"text":":timer_clock:Wait time: %02d:%02d:%02d\n:zap:Surge Multiplier: %s" % (h, m, s, surgeMultiplier),
													"title":display_name,
													"footer_icon":"https://lh3.googleusercontent.com/HN6oUA-upH3oPTvP95JQX_Yr9QeCkFnUlEn0U2XgoV9fZSOLldad1eIWln6FR1PEQ20=w196",
													"footer":"Brought to you by your friends at Surf!"
													}]
									}))
				return HttpResponse(status=201)

			else:

				print "seems service is unavailable here.."

				return JsonResponse({"text": "Sorry friend, seems Uber is unavailable at the coordinates you provided me.  Please try with a different location, or with (%s, %s) later on.  :car:"%(lat,lng)})


			#return JsonResponse({"text":"Sorry friend, this will be an awesome feature, I promise you.  But I'm not quite ready yet.  Thanks for thinking of me. :kissing_heart:"})

		else:
			return JsonResponse({"text":"Sorry friend, I'm not programmed to respond to \"%(input_text)s\" yet.  Try 'help' for a list of available commands. :surfer:"%{'input_text': text[0]}})


def authCalendar(request):

    print "Loading GCal Auth page."

    print request

    if request.method == "GET":
        print request.GET
    else:
        print request.POST

    return render(request, 'google-auth.html')

    print "GCal Auth loaded with no problems."


def authCalendarSuccess(request):

    print "got a good GCal auth coming back"

    render(request, 'google-auth-success.html')


def catchToken(request):

    print "Receiving successful GCal Auth callback"
    print request
    inputs = dict(request.GET)
    print inputs

    try:
        print inputs['access_token']
    except:
        print "no access_token"
    try:
        print inputs['expires_in']
    except:
        print "no expires_in"
    try:
        print inputs['token_type']
    except:
        print "no token_type"


def auth(request):

	print "Loading Auth page."

	return render(request, 'base.html')

	print "Auth page loaded with no problems."
