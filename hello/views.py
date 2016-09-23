from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
import json, random, requests, os, psycopg2, urlparse, uuid
from django.views.decorators.csrf import csrf_exempt

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
google_api_key = os.environ['GCAL_API_KEY']
access_token = os.environ['GCAL_ACCESS_TOKEN_TAYLOR']

## URL for pinging myself in Slack
mySlackWebhookUrl = os.environ['SLACK_WEBHOOK_URL']
slackClientId = os.environ['SLACK_CLIENT_ID']
slackClientSecret = os.environ['SLACK_CLIENT_SECRET']
slackTestToken = os.environ['SLACK_TEST_TOKEN']

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
print "connected to appbackr DB"
cur = conn.cursor()

updateAccessToken = """UPDATE google_calendar_access_tokens
						SET access_token=%(access_token)s, updated_at=now(), refresh_token=%(refresh_token)s
						WHERE id=1"""
updateOnlyAccessToken = "UPDATE google_calendar_access_tokens SET access_token=%(access_token)s, updated_at=now() WHERE refresh_token=%(refresh_token)s"
insertNewAccessToken = """INSERT INTO google_calendar_access_tokens (access_token, token_type, expires_in, created_at, updated_at, refresh_token)
							VALUES (%(access_token)s, %(token_type)s, %(expires_in)s, now(), now(), %(refresh_token)s)"""
updateUserData = """UPDATE google_calendar_access_tokens
					SET primary_calendar=%(primary_calendar)s, updated_at=now(), resource_uri=%(resource_uri)s, resource_id=%(resource_id)s, resource_uuid=%(resource_uuid)s
					WHERE access_token=%(access_token)s"""
getAccessToken = """SELECT access_token
					FROM google_calendar_access_tokens
					WHERE resource_uri=%(resource_uri)s AND resource_uuid=%(resource_uuid)s AND resource_id=%(resource_id)s"""
getAccessTokenAndSyncToken = """SELECT access_token, next_sync_token
								FROM google_calendar_access_tokens
								WHERE resource_uri=%(resource_uri)s AND resource_uuid=%(resource_uuid)s AND resource_id=%(resource_id)s"""
saveNextSyncToken = """UPDATE google_calendar_access_tokens
						SET next_sync_token=%(next_sync_token)s, updated_at=now()
						WHERE resource_uri=%(resource_uri)s AND resource_uuid=%(resource_uuid)s AND resource_id=%(resource_id)s"""
insertNewUser = """INSERT INTO google_calendar_users (user_name, image_url, email) VALUES (%(user_name)s, %(image_url)s, %(email)s)"""
selectExistingUser = "SELECT id FROM google_calendar_users WHERE user_name=%(user_name)s AND email=%(email)s"

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

	if 'text' not in inputs:
		return render(request, 'home.html')

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


def authCalendarSuccess(request):

	print "got a good GCal auth coming back"

	inputs = dict(request.GET)
	print "inputs: ", inputs
	print "body: ", request.body
	#print "headers: ", request.META

	tempCode = inputs['code'][0]

	## exchange CODE for TOKEN
	exchangeCodeForToken = "https://www.googleapis.com/oauth2/v4/token"
	## info: https://developers.google.com/identity/protocols/OAuth2WebServer

	response = requests.post(exchangeCodeForToken, data={'code':tempCode, 'client_id':GCalClientId, 'client_secret':GCalClientSecret, 'redirect_uri':'https://surfy-surfbot.herokuapp.com/auth-cal-success', 'grant_type':'authorization_code'})
	print response
	print "response headers: ",response.headers
	authData = response.json()
	print "response json: ", authData

	try:
		refreshToken = authData['refresh_token']
	except:
		refreshToken = None
	tokenType = authData['token_type']
	expiresIn = authData['expires_in']
	accessToken = authData['access_token']

	## log to server for later use
	cur.execute(insertNewAccessToken, {'access_token':accessToken, 'refresh_token':refreshToken, 'token_type':tokenType, 'expires_in':expiresIn})
	conn.commit()
	print "New access token successfully stored!"

	print "calling watch calendar method"

	calendar = getCalendars(accessToken)

	if calendar is not None:

		success, resource_uri, resource_id, resource_uuid = askWatchCalendar(calendar, accessToken)

		if success:
			cur.execute(updateUserData, {'primary_calendar':calendar, 'resource_uri':resource_uri, 'access_token':accessToken, 'resource_id':resource_id, 'resource_uuid':resource_uuid})
			conn.commit()
			return HttpResponse('%s is now being watched!'%calendar)
		else:
			return HttpResponse('There seems to have been an error... Please try again.')

	else:
		return HttpResponse('Failed to find the primary calendar for this user...')


def askWatchCalendar(calendar, access_token):

	print "asking for permission to watch calendar"

	#cur.execute(getAccessToken,)
	#access_token = cur.fetchone()[0]
	#print "access_token: ", access_token

	response = requests.post("https://www.googleapis.com/calendar/v3/calendars/"+calendar+"/events/watch",
								headers={'Authorization':'Bearer '+access_token, 'Content-Type': 'application/json'},
								data=json.dumps({'id':str(uuid.uuid4()), 'type':'web_hook', 'address':'https://surfy-surfbot.herokuapp.com/receive-gcal'}))
	print response
	watchData = response.json()
	print "watchData: ", watchData

	if response.status_code == 200:

		resource_uri = watchData['resourceUri']
		resource_id = watchData['resourceId']
		resource_uuid = watchData['id']

		return True, resource_uri, resource_id, resource_uuid
	else:
		return False


def getCalendars(access_token):

	print "Fetching Calendars List for user"

	#cur.execute(getAccessToken,)
	#access_token = cur.fetchone()[0]
	#print "access_token: ", access_token

	calendarListUrl = "https://www.googleapis.com/calendar/v3/users/me/calendarList" ## GET

	#response = requests.get(calendarListUrl, headers={'Authorization':'OAuth '+access_token, 'Content-Type': 'application/json'}, params={'access_token':access_token, 'key':google_api_key})
	response = requests.get(calendarListUrl, headers={'Content-Type': 'application/json'}, params={'access_token':access_token})
	if response.status_code == 200:

		responseData = response.json()
		print "response: ", responseData

		for calendar in responseData['items']:

			if 'primary' in calendar and calendar['primary'] == True:

				return calendar['id']

	return None


def getEvent(event_id, uri, access_token):

	print "Fetching Calendar Event for user"

	eventUrl = uri.strip('?alt=json')+"/"+event_id

	response = requests.get(eventUrl, headers={'Content-Type': 'application/json'}, params={'access_token':access_token})

	if response.status_code == 200:
		eventDetails = response.json()
		print "eventDetails: ", eventDetails
	else:
		print response
		print "headers: ", response.headers
		print "text: ", response.text


def getAllEvents(uri, uuid, resource_id):

	print "Fetching all Calendar Events for user"

	cur.execute(getAccessToken, {'resource_uri':uri, 'resource_uuid':uuid, 'resource_id':resource_id})
	access_token = cur.fetchone()[0]

	response = requests.get(uri, headers={'Content-Type': 'application/json'}, params={'access_token':access_token, 'maxResults':10})

	if response.status_code == 200:
		responseData = response.json()
		print "response: ", responseData

		next_sync_token = responseData['nextSyncToken']
		print "next_sync_token: ", next_sync_token

		cur.execute(saveNextSyncToken, {'next_sync_token':next_sync_token, 'resource_uri':uri, 'resource_uuid':uuid, 'resource_id':resource_id})
		conn.commit()
		print "next_sync_token saved."


def getNewEvents(uri, uuid, resource_id):

	print "Updating Events since last sync"

	# access_token, sync_token needed
	cur.execute(getAccessTokenAndSyncToken, {'resource_uri':uri, 'resource_uuid':uuid, 'resource_id':resource_id})
	tokens = cur.fetchone()
	if tokens is not None:
		access_token = tokens[0]
		sync_token = tokens[1]
	else:
		print "unable to grab access_token and sync_token from database... have I seen this user before?"
		return

	response = requests.get(uri, headers={'Content-Type':'application/json'}, params={'access_token':access_token, 'syncToken':sync_token})

	if response.status_code == 200:

		newEvents = response.json()
		print "newEvents: ", newEvents

		if 'nextSyncToken' in newEvents:
			next_sync_token = newEvents['nextSyncToken']
			print "next_sync_token: ", next_sync_token

			cur.execute(saveNextSyncToken, {'next_sync_token':next_sync_token, 'resource_uri':uri, 'resource_uuid':uuid, 'resource_id':resource_id})
			conn.commit()
			print "next_sync_token saved."

		if 'items' in newEvents and newEvents['items'] != []:
			for event in newEvents['items']:
				eventId = event['id']
				if event['kind'] == 'calendar#event':
					#getEvent(eventId, uri, access_token)
					pass
		else:
			print "no new events"
	elif response.status_code == 401:
		print "outdated access_token\nCalling refresh method"
		access_token = refreshAuthToken(access_token)
		response = requests.get(uri, headers={'Content-Type':'application/json'}, params={'access_token':access_token, 'syncToken':sync_token})
		if response.status_code == 200:
			newEvents = response.json()
			print "newEvents: ", newEvents

			if 'nextSyncToken' in newEvents:
				next_sync_token = newEvents['nextSyncToken']
				print "next_sync_token: ", next_sync_token

				cur.execute(saveNextSyncToken, {'next_sync_token':next_sync_token, 'resource_uri':uri, 'resource_uuid':uuid, 'resource_id':resource_id})
				conn.commit()
				print "next_sync_token saved."

			if 'items' in newEvents and newEvents['items'] != []:
				for event in newEvents['items']:
					eventId = event['id']
					if event['kind'] == 'calendar#event':
						#getEvent(eventId, uri, access_token)
						pass
					else:
						print "no new events"
		else:
			print "still have invalid auth token .. giving up"
			print "headers: ", response.headers
			print "text: ", response.text
	else:

		print response
		print "headers: ", response.headers
		print "text: ", response.text


@csrf_exempt
def refreshAuthToken(access_token):

	print "refreshing auth token"

	refreshUrl = "https://www.googleapis.com/oauth2/v4/token" ## POST

	## get refresh token from server
	selectRefreshToken = "SELECT refresh_token FROM google_calendar_access_tokens WHERE access_token=%(access_token)s"
	cur.execute(selectRefreshToken, {'access_token':access_token})
	data = cur.fetchone()
	if data is not None and data[0] is not None:
		refresh_token = data[0]
	else:
		print "error retrieving refresh_token from server for access_token: %s"%access_token
		print "need the user to re-auth calendar access"
		## really I should be using a specific param to ask for new refresh_token as well..
		## set prompt=consent in the offline access step (https://developers.google.com/identity/protocols/OAuth2WebServer#refresh)
		return render('google-auth.html')


	response = requests.post(refreshUrl, data={'client_id':GCalClientId, 'client_secret':GCalClientSecret, 'refresh_token':refresh_token, 'grant_type':'refresh_token'})
	if response.status_code == 200:
		newData = response.json()
		access_token = newData['access_token']
		expires_in = newData['expires_in']
		token_type = newData['token_type']

		## now update server
		cur.execute(updateOnlyAccessToken, {'access_token':access_token, 'refresh_token':refresh_token})
		conn.commit()
		print "new access_token saved!"

		return access_token

	else:
		print "error refreshing token"
		print "headers: ", response.headers
		print "text: ", response.text


@csrf_exempt
def catchNewGoogleUser(request):

	print "New Google User incoming"

	print request
	inputs = json.loads(request.body)
	print "body: ", inputs

	## now insert into users table
	try:
		user_name = inputs['user_name']
	except:
		user_name = None
	try:
		image_url = inputs['image_url']
	except:
		image_url = None
	try:
		email = inputs['email']
	except:
		email = None
	#user_name = inputs['user_name']
	#image_url = inputs['image_url']
	#email = inputs['email']

	cur.execute(selectExistingUser, {'user_name':user_name, 'email':email})
	existingId = cur.fetchone()

	if existingId is None or existingId[0] is None:
		cur.execute(insertNewUser, {'user_name':user_name, 'image_url':image_url, 'email':email})
		conn.commit()
		print "new User submitted"
		return JsonResponse({'new_user':True})
	else:
		print "I already have this User logged as: %s"%existingId
		return JsonResponse({'new_user':False})


@csrf_exempt
def receiveGcal(request):

	print "receiving GCal ping now!"
	print request
	if request.method == 'GET':
		print request.GET
	else:
		print request.POST

	print "printing body text"

	try:
		print "body: ", request.body
	except:
		print "no request.body"

	print "printing headers"
	headers = request.META
	print "headers: ", headers

	try:
		googleResourceUri = headers['HTTP_X_GOOG_RESOURCE_URI']
		print "googleResourceUri: ", googleResourceUri
		googleResourceState = headers['HTTP_X_GOOG_RESOURCE_STATE']
		print "googleResourceState: ", googleResourceState
		googleResourceId = headers['HTTP_X_GOOG_RESOURCE_ID']
		print "googleResourceId: ", googleResourceId
		googleChannelId = headers['HTTP_X_GOOG_CHANNEL_ID']
		print "googleChannelId: ", googleChannelId
		googleMessageNumber = headers['HTTP_X_GOOG_MESSAGE_NUMBER']
		print "googleMessageNumber: ", googleMessageNumber
	except:
		print "error parsing Google Resources..."
		googleResourceState = 'fail'

	if googleResourceState == 'sync':
		#getAllEvents(googleResourceUri, googleChannelId, googleResourceId)
		print "sync..passing"

	elif googleResourceState == 'exists':
		getNewEvents(googleResourceUri, googleChannelId, googleResourceId)

		## ping myself in Slack
		response = requests.post('https://slack.com/api/chat.postMessage', params={
																	"text": "Would you like to play a game?",
																	"attachments": json.dumps([
																		{
																			"text": "Choose a game to play",
																			"fallback": "You are unable to choose a game",
																			"callback_id": "wopr_game",
																			"color": "#3AA3E3",
																			"attachment_type": "default",
																			"actions": [
																				{
																					"name": "chess",
																					"text": "Chess",
																					"type": "button",
																					"value": "chess"
																				},
																				{
																					"name": "maze",
																					"text": "Falken's Maze",
																					"type": "button",
																					"value": "maze"
																				},
																				{
																					"name": "war",
																					"text": "Thermonuclear War",
																					"style": "danger",
																					"type": "button",
																					"value": "war",
																					"confirm": {
																						"title": "Are you sure?",
																						"text": "Wouldn't you prefer a good game of chess?",
																						"ok_text": "Yes",
																						"dismiss_text": "No"
																					}
																				}
																			]
																		}
																	]),
																	"channel":"@taylor",
																	"token":slackTestToken
																},
																headers={"Content-Type":"application/json"})
		#if response.status_code != 200:
		print response
		print "data:", response.json()

	return HttpResponse("OK")


@csrf_exempt
def slackButtons(request):

	print "Response to Slack Button incoming."
	print "POST:", request.POST
	print "Headers:", request.META
	print "Body:", request.body


def auth(request):

	inputs = dict(request.GET)
	print "inputs:", inputs
	print "code:", inputs['code']
	print "state:", inputs['state']

	## take code, request auth_token
	slackAuthUrl = 'https://slack.com/api/oauth.access'
	response = requests.get(slackAuthUrl, params={'code':inputs['code'], 'client_id':slackClientId, 'client_secret':slackClientSecret})
	print response
	responseData = response.json()
	print "data:", responseData
	print "auth token:", responseData['access_token']

	print "Loading Auth page."

	return render(request, 'base.html')

	print "Auth page loaded with no problems."
