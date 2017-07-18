from django.conf.urls import patterns, include, url

urlpatterns = patterns('home.views',
    url(r'^$', 'home', name='home'),
    url(r'^testruns/$', 'testruns', name='testruns'),
    url(r'^testruns/new/$', 'new_testrun', name='new_testrun'),
    url(r'^testruns/(?P<pk>\d+)/$', 'show_testrun', name='show_testrun'),
    url(r'^testruns/(?P<pk>\d+)/reschedule/$', 'reschedule_testrun', name='reschedule_testrun'),

    # Testsuite URLs
    url(r'^suites/$', 'show_testsuite', name='show_testsuite'),
    url(r'^suites/new/$', 'new_testsuite', name='new_testsuite'),
    url(r'^suites/edit/$', 'edit_testsuite', name='edit_testsuite'),
    url(r'^suites/delete/$', 'delete_testsuite', name='delete_testsuite'),

    # Testbed URLs
    url(r'^testbeds/$', 'show_testbed', name='show_testbed'),
    url(r'^testbeds/new/$', 'new_testbed', name='new_testbed'),
    url(r'^testbeds/edit/$', 'edit_testbed', name='edit_testbed'),
    url(r'^testbeds/delete/$', 'delete_testbed', name='delete_testbed'),

    url(r'^logs/(?P<path>.+)/$', 'show_logs', name='show_logs'),
)
