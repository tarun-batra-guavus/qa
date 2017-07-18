"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

Code for admin pages of this app
"""
from django.contrib import admin
from .models import Solution, Build, TestsuiteExecution, TestcaseExecution

class SolutionAdmin(admin.ModelAdmin):
    pass
admin.site.register(Solution, SolutionAdmin)

class BuildAdmin(admin.ModelAdmin):
    pass
admin.site.register(Build, BuildAdmin)

class TestsuiteExecutionAdmin(admin.ModelAdmin):
    pass
admin.site.register(TestsuiteExecution, TestsuiteExecutionAdmin)

class TestcaseExecutionAdmin(admin.ModelAdmin):
    pass
admin.site.register(TestcaseExecution, TestcaseExecutionAdmin)
