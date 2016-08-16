from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
import json, random, requests, os, psycopg2, urlparse

## appbackr Endorsement URL [requires package_name & api_key & auth_token]
endorsementUrl = "https://index.appbackr.com/v1/endorsements"
appbackrApiKey = "20fe813188a344f9a29fd22d69f789d9"
appbackrAuthToken = "f70dfa1917c6b3e3e6fb2807e2b65ca5"

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
				packageName = text[1].lower()
			except:
				## if this fails it should be because I wasn't given a second text param, i.e. not given a package name
				return JsonResponse({"text":"Sorry, but for me to return you an endorsement, I'll need to know what app you'd like to learn about.\nPlease provide me an Android ID (aka Package Name) like this `/surf endorsement com.Slack`. :calling:"})

			print "Calling Endorsement URL for package_name:",packageName
			endorsementResponse = requests.get(endorsementUrl, params={'package_name':packageName, 'api_key':appbackrApiKey, 'auth_token': appbackrAuthToken})

			print "endorsementResponse status code:",endorsementResponse.status_code
			print "endorsementResponse json:",endorsementResponse.json()

			return JsonResponse({"text":"Here's what I got:\n>%s"%endorsementResponse.json()})

			#requests.post(responseUrl, data=json.dumps({"text":"Master @%(username)s says: %(wow_message)s"%{'username':inputs['user_name'][0], 'wow_message':wow_message}, "response_type":"in_channel"}))
			#return HttpResponse(status=201)
		
		#elif thyBidding == 'stuff2':
		
		#elif thyBidding == 'stuff3':

		else:
			return JsonResponse({"text":"Sorry friend, I'm not programmed to respond to \"%(input_text)s\" yet.  Try 'help' for a list of available commands. :surfer:"%{'input_text': text[0]}})







def auth(request):

	print "Loading Auth page."

	return render(request, 'base.html')

	print "Auth page loaded with no problems."