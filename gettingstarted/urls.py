from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import hello.views

# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', hello.views.index, name='index'),
    url(r'^auth-calendar', hello.views.authCalendar, name='authCalendar'),
    url(r'^auth-cal-success', hello.views.authCalendarSuccess, name='authCalendarSuccess'),
    url(r'^auth', hello.views.auth, name='auth'),
    url(r'^catchNewGoogleUser', hello.views.catchNewGoogleUser, name='catchNewGoogleUser'),
    #url(r'^catchtoken', hello.views.catchToken, name='catchToken'),
    url(r'^receive-gcal', hello.views.receiveGcal, name='receiveGcal'),
    url(r'^slack-buttons', hello.views.slackButtons, name='slackButtons')
    #url(r'^admin/', include(admin.site.urls)),
]
