"""
.. moduleauthor:: Sandeep Nanda <sandeep.nanda@guavus.com>

Views used by Potluck Web UI
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory

import os
import re

from .models import TestsuiteExecution, Build
from .forms import TestsuiteExecutionForm, NodeForm, BaseNodeFormset, TestbedForm, TestcaseForm, BaseTestsuiteFormset, TestsuiteForm
from potluck.utils import parse_suite_xml, parse_testbed
from utils import find_all_files, check_testbed_owner, process_logs_for_html

def home(request):
    test_executions = TestsuiteExecution.objects.order_by("started_at").reverse()[:10]
    return render(request, "home/home.html", {
                    "test_executions" : test_executions,
                    "builds" : Build.objects.all()})

def testruns(request):
    test_executions = TestsuiteExecution.objects.order_by("started_at").reverse()[:50]
    return render(request, "home/testruns.html", {"test_executions" : test_executions})

@login_required
def new_testrun(request):
    if request.method == "POST":
        testrun_form = TestsuiteExecutionForm(data=request.POST, user=request.user)
        if testrun_form.is_valid():
            testrun_form.save()
            messages.success(request, "Successfully scheduled testrun for build '%s' with testsuite '%s'" % (testrun_form.cleaned_data["build"], testrun_form.cleaned_data["suite"]))
            return redirect("testruns")
    else:
        testrun_form = TestsuiteExecutionForm(user=request.user)
    return render(request, "home/new_testrun.html", {"form" : testrun_form})

@login_required
def reschedule_testrun(request, pk):
    execution = get_object_or_404(TestsuiteExecution, pk=pk)
    try:
        new_execution = execution.reschedule(user=request.user)
        messages.success(request, "Successfully scheduled testrun for build '%s' with testsuite '%s' on testbed '%s'" % 
                                    (new_execution.build, new_execution.suite, new_execution.testbed))
    except Exception as e:
        messages.error(request, str(e))
    return redirect("testruns")

def show_testrun(request, pk):
    execution = get_object_or_404(TestsuiteExecution, pk=pk)
    return render(request, "home/show_testrun.html", {"execution" : execution})

def show_testsuite(request):
    path = request.REQUEST.get("testsuite")
    testsuite = parse_suite_xml(path)
    if request.is_ajax():
        template = "home/_show_testsuite.html"
    else:
        template = "home/show_testsuite.html"
    return render(request, template, {"testsuite" : testsuite, "testsuite_name" : path})

def show_testbed(request):
    path = request.REQUEST.get("testbed")
    testbed = parse_testbed(path)
    if request.is_ajax():
        template = "home/_show_testbed.html"
    else:
        template = "home/show_testbed.html"
    return render(request, template, {"testbed" : testbed, "testbed_name" : path})

NodeFormset = formset_factory(NodeForm, formset=BaseNodeFormset, extra=1)
@login_required
def new_testbed(request):
    if request.method == "POST":
        testbed_form = TestbedForm(request.POST, user=request.user, prefix="testbed")
        formset = NodeFormset(request.POST, prefix="nodes")

        # Both testbed name and node list should be valid
        if testbed_form.is_valid() and formset.is_valid():
            formset.create_testbed_file(testbed_form.testbed_path)   # Create the actual testbed file
            messages.success(request, "Created Testbed")
            return redirect("edit_testbed")
    else:
        formset = NodeFormset(prefix="nodes")
        testbed_form = TestbedForm(prefix="testbed")
    return render(request, "home/new_edit_testbed.html", {"formset" : formset, "testbed_form" : testbed_form})

@login_required
def delete_testbed(request):
    if "testbed" in request.GET:
        testbed_name = request.GET.get("testbed")
        if not check_testbed_owner(testbed_name, request.user):
            logging.warning("%s is not the owner of testbed '%s'" % (request.user.username, testbed_name))
            messages.error(request, "You are not the owner of this testbed")
        else:
            testbed_path = os.path.join(settings.POTLUCK.USER_TESTBEDS_DIR, testbed_name)
            try:
                os.remove(testbed_path)
                messages.success(request, "Successfully deleted testbed '%s'" % testbed_name)
            except Exception as e:
                messages.error(request, "Error: %s" % str(e))
    else:
        messages.error(request, "No testbed mentioned")
    return redirect("edit_testbed")

@login_required
def edit_testbed(request):
    if request.method == "POST":
        testbed_form = TestbedForm(request.POST, user=request.user, overwrite=True, prefix="testbed")
        formset = NodeFormset(request.POST, prefix="nodes")

        # Both testbed name and node list should be valid
        if testbed_form.is_valid() and formset.is_valid():
            formset.create_testbed_file(testbed_form.testbed_path)   # Create the actual testbed file
            messages.success(request, "Successfully saved testbed")
            return redirect("edit_testbed")
    else:
        # If no `GET` parameter is defined, then show the testbed names
        if "testbed" in request.GET:
            testbed_name = request.GET.get("testbed")
            if not check_testbed_owner(testbed_name, request.user):
                logging.warning("%s is not the owner of testbed '%s'" % (request.user.username, testbed_name))
                messages.error(request, "You are not the owner of this testbed")
                return redirect("edit_testbed")

            testbed_path = os.path.join(settings.POTLUCK.USER_TESTBEDS_DIR, testbed_name)
            if os.path.exists(testbed_path):
                testbed = parse_testbed(testbed_name)
                if not testbed:
                    messages.error(request, "Error reading Testbed. Please delete and add a new testbed.")
                    return redirect("edit_testbed")

                # Remove the username from the testbed name
                testbed_name = re.sub("^%s/" % request.user.username, "", testbed_name)
                testbed_form = TestbedForm(initial={"name" : testbed_name}, prefix="testbed")

                # Populate the nodes data
                initial_nodes_data = [{
                        "alias" : node["alias"],   
                        "ip" : node["ip"],
                        "components" : ",".join(node["type"]),
                        "password" : node["password"]
                        } for node in testbed.values()]
                formset = NodeFormset(initial=initial_nodes_data, prefix="nodes")
            else:
                messages.error(request, "Testbed does not exist")
                user_dir = os.path.join(settings.POTLUCK.USER_TESTBEDS_DIR, request.user.username)
                user_testbeds = find_all_files(user_dir)
                return render(request, "home/show_testbeds_for_edit.html", {"user_testbeds" : user_testbeds})
        else:
            user_dir = os.path.join(settings.POTLUCK.USER_TESTBEDS_DIR, request.user.username)
            user_testbeds = find_all_files(user_dir)
            return render(request, "home/show_testbeds_for_edit.html", {"user_testbeds" : user_testbeds})
    testbed_form.fields["name"].widget.attrs["readonly"] = True
    return render(request, "home/new_edit_testbed.html", {"formset" : formset, "testbed_form" : testbed_form, "is_edit": True})

def show_logs(request, path):
    logs_path = os.path.join(settings.POTLUCK.LOGS_DIR, path)
    if os.path.exists(logs_path):
        with open(logs_path) as fh:
            logs = process_logs_for_html(fh)
    else:
        messages.error(request, "Log file does not exist")
        logs = ""

    if request.is_ajax():
        template = "home/_show_logs.html"
    else:
        template = "home/show_logs.html"
    return render(request, template, {"logs" : logs})

TestsuiteFormset = formset_factory(TestcaseForm, formset=BaseTestsuiteFormset, extra=1, can_order=True)
@login_required
def new_testsuite(request):
    if request.method == "POST":
        testsuite_form = TestsuiteForm(request.POST, user=request.user, prefix="testsuite")
        formset = TestsuiteFormset(request.POST, prefix="testcase")

        # Both testsuite name and node list should be valid
        if testsuite_form.is_valid() and formset.is_valid():
            formset.create_file(testsuite_form.path)   # Create the actual testsuite file
            messages.success(request, "Successfully created new Testsuite")
            return redirect("edit_testsuite")
    else:
        formset = TestsuiteFormset(prefix="testcase")
        testsuite_form = TestsuiteForm(prefix="testsuite")
    return render(request, "home/new_edit_testsuite.html", {"formset" : formset, "testsuite_form" : testsuite_form})

@login_required
def edit_testsuite(request):
    if request.method == "POST":
        testsuite_form = TestsuiteForm(request.POST, user=request.user, overwrite=True, prefix="testsuite")
        formset = TestsuiteFormset(request.POST, prefix="testcase")

        # Both testsuite name and node list should be valid
        if testsuite_form.is_valid() and formset.is_valid():
            formset.create_file(testsuite_form.path)   # Create the actual testsuite file
            messages.success(request, "Successfully saved testsuite")
            return redirect("edit_testsuite")
    else:
        # If no `GET` parameter is defined, then show the testsuite names
        if "testsuite" in request.GET:
            testsuite_name = request.GET.get("testsuite")
            if not check_testbed_owner(testsuite_name, request.user):
                logging.warning("%s is not the owner of testsuite '%s'" % (request.user.username, testsuite_name))
                messages.error(request, "You are not the owner of this testsuite")
                return redirect("edit_testsuite")

            testsuite_path = os.path.join(settings.POTLUCK.USER_SUITES_DIR, testsuite_name)
            if os.path.exists(testsuite_path):
                testsuite = parse_suite_xml(testsuite_name, relative_paths=True)
                if not testsuite:
                    messages.error(request, "Error reading Testsuite. Please delete and add a new suite.")
                    return redirect("edit_testsuite")

                # Populate the nodes data
                initial_testcases_data = [{
                        "section" : sec["name"],   
                        "script" : tc["script"],   
                        "rule" : tc["rule"],
                        } for sec in testsuite["sections"] for tc in sec["testcases"]]

                # Remove the username from the testsuite name
                testsuite_name = re.sub("^%s/" % request.user.username, "", testsuite_name)
                testsuite_form = TestsuiteForm(initial={"name" : testsuite_name}, prefix="testsuite")

                print initial_testcases_data
                formset = TestsuiteFormset(initial=initial_testcases_data, prefix="testcase")
            else:
                messages.error(request, "Testsuite does not exist")
                return redirect("edit_testsuite")
        else:
            user_dir = os.path.join(settings.POTLUCK.USER_SUITES_DIR, request.user.username)
            user_testsuites = find_all_files(user_dir)
            return render(request, "home/show_testsuites_for_edit.html", {"user_testsuites" : user_testsuites})
    testsuite_form.fields["name"].widget.attrs["readonly"] = True
    return render(request, "home/new_edit_testsuite.html", {"formset" : formset, "testsuite_form" : testsuite_form, "is_edit": True})

@login_required
def delete_testsuite(request):
    if "testsuite" in request.GET:
        testsuite_name = request.GET.get("testsuite")
        if not check_testbed_owner(testsuite_name, request.user):
            logging.warning("%s is not the owner of testsuite '%s'" % (request.user.username, testsuite_name))
            messages.error(request, "You are not the owner of this testsuite")
        else:
            testsuite_path = os.path.join(settings.POTLUCK.USER_SUITES_DIR, testsuite_name)
            try:
                os.remove(testsuite_path)
                messages.success(request, "Successfully deleted testsuite '%s'" % testsuite_name)
            except Exception as e:
                messages.error(request, "Error: %s" % str(e))
    else:
        messages.error(request, "No testsuite mentioned")
    return redirect("edit_testsuite")
