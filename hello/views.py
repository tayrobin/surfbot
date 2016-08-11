from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
import json, random, requests
import os
import psycopg2
import urlparse

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
	if request.method == 'GET':
		print "Order up!"
		print request.GET
		inputs = dict(request.GET)

		selectTaylorUserId = "SELECT id FROM users WHERE username=%(username)s"
		cur.execute(selectTaylorUserId, {'username':'taylor'})
		taylorUserId = cur.fetchone()[0]

		return JsonResponse({"text":"username %(username)s has user id %(user_id)s"%{"username":'taylor', "user_id":taylorUserId}})