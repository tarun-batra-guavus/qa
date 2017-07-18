"""
.. moduleauthor:: Sandeep Nanda <sandeep.nanda@guavus.com>

Forms and methods used by Potluck Web UI
"""

from django import forms
from django.conf import settings
from django.forms.formsets import BaseFormSet
from django.core.validators import RegexValidator

import os
import logging
import re
import xml.etree.ElementTree as ET
import xml.dom.minidom

from .models import TestsuiteExecution
from utils import find_all_files
from potluck.utils import parse_suite_xml, has_ui_testcases

no_spaces_re = re.compile(r'^[-a-zA-Z0-9_\.]+$')
validate_no_spaces = RegexValidator(no_spaces_re, "This field can consist of letters, numbers, underscores or hyphens.", 'invalid')

logger = logging.getLogger(__name__)

def _choices_to_groups(choices, empty=False, empty_text="-------"):
    suite_choices = []
    group_choices = []
    last_group = None
    if empty is True:
        suite_choices.append((None, empty_text))

    for f in choices:
        group = f.split(os.sep)[0] if os.sep in f else ""
        group = group.title()
        if group != last_group and last_group is not None:
            suite_choices.append((last_group, group_choices))
            group_choices = []
        group_choices.append((f, f))
        last_group = group
    suite_choices.append((last_group, group_choices))
    return suite_choices

def _extract_sikuli_path(filepath):
    if ".sikuli" not in filepath:
        return filepath
    
    return os.sep.join(filepath.split(os.sep)[:-1])

# Create the form class.
class TestsuiteExecutionForm(forms.ModelForm):
    class Meta:
        model = TestsuiteExecution
        fields = ['build', 'suite', 'testbed', 'ui_url']

    suite = forms.ChoiceField()
    testbed = forms.ChoiceField()

    def __init__(self, user, *args, **kwargs):
        super(TestsuiteExecutionForm, self).__init__(*args, **kwargs)
        suites = find_all_files(settings.POTLUCK.SUITES_DIR)
        suites += find_all_files(settings.POTLUCK.USER_SUITES_DIR)
        testbeds = find_all_files(settings.POTLUCK.TESTBEDS_DIR)
        testbeds += find_all_files(settings.POTLUCK.USER_TESTBEDS_DIR)
        self.parsed_suite = None
        self.user = user
        #self.fields["testbed"].choices = ((f, f.title()) for f in testbeds)
        self.fields["suite"].choices = _choices_to_groups(suites)
        self.fields["testbed"].choices = _choices_to_groups(testbeds)

    def save(self, commit=True):
        new_testrun = super(TestsuiteExecutionForm, self).save(commit=False)
        new_testrun.user = self.user
        if commit is True:
            new_testrun.save()
        return new_testrun

    def clean(self):
        # Check UI URL here, because we need to make sure that clean_suite has already executed
        if self.parsed_suite is not None and has_ui_testcases(self.parsed_suite) is True:
            ui_url = self.cleaned_data.get("ui_url", None)
            if not ui_url:
                logger.warning("UI URL is not passed for a UI based testsuite")
                self.add_error("ui_url", "Url of the UI is mandatory for this testsuite, because it has sikuli based testcases")
            elif not ui_url.startswith("https://"):
                self.add_error("ui_url", "Url should start with https://")
        return self.cleaned_data

    def clean_suite(self):
        path = self.cleaned_data["suite"]
        try:
            self.parsed_suite = parse_suite_xml(path)
        except Exceptions as e:
            raise forms.ValidationError(str(e))

        if not self.parsed_suite:
            raise forms.ValidationError("Testsuite is empty")

        return path

SUPPORTED_COMPONENTS = ("namenode", "insta", "rge", "rubix", "datanode", "collector")
class NodeForm(forms.Form):
    alias = forms.CharField(validators=[validate_no_spaces])
    ip = forms.GenericIPAddressField(protocol="IPv4")
    components = forms.CharField()
    password = forms.CharField()

    def clean_components(self):
        components = self.cleaned_data["components"]
        component_list = []
        for component in components.lower().split(","):
            component = component.strip()
            if not component:
                continue
            elif component not in SUPPORTED_COMPONENTS:
                raise forms.ValidationError("Invalid value '%s'. Supported types are %s" % (component, ", ".join(SUPPORTED_COMPONENTS)))
            elif component not in component_list:
                # De-dupe components
                component_list.append(component)
        return ",".join(component_list)

class TestbedForm(forms.Form):
    name = forms.CharField(label="Testbed Name", validators=[validate_no_spaces])

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.overwrite = kwargs.pop("overwrite", False)
        super(TestbedForm, self).__init__(*args, **kwargs)

    @property
    def testbed_path(self):
        if not hasattr(self, "_testbed_path"):
            testbed_name = self.cleaned_data["name"]
            # Make sure the testbed is created in the user's directory
            self._testbed_path = os.path.join(settings.POTLUCK.USER_TESTBEDS_DIR, self.user.username, testbed_name)
        return self._testbed_path
        
    def clean(self):
        cleaned_data = super(TestbedForm, self).clean()

        # Validate path existence only if a valid name was passed
        if "name" in cleaned_data and self.overwrite is not True and os.path.exists(self.testbed_path):
            raise forms.ValidationError("Testbed already exists. Please choose a different name or go to edit page to modify the testbed")

        return self.cleaned_data

class BaseNodeFormset(BaseFormSet):
    def clean(self):
        """Checks that no two nodes have the same alias or ip."""
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        if self.total_form_count() <= 0:
            raise forms.ValidationError("Minimum one node is required")

        # Check that same alias is not passed for multiple nodes
        alias_list = []
        ip_list = []
        for form in self.forms:
            alias = form.cleaned_data["alias"]
            ip = form.cleaned_data["ip"]
            if alias in alias_list:
                raise forms.ValidationError("Alias '%s' is used for multiple nodes. Please use unique aliases." % alias)
            elif ip in ip_list:
                raise forms.ValidationError("IP '%s' is used for multiple nodes. Please use unique IPs." % ip)
            else:
                alias_list.append(alias)
                ip_list.append(ip)
        return self.cleaned_data

    def create_testbed_file(self, testbed_file):
        import ConfigParser
        config = ConfigParser.RawConfigParser()

        testbed_dir = os.path.dirname(testbed_file)
        if not os.path.exists(testbed_dir):
            os.makedirs(testbed_dir)

        for form_data in self.cleaned_data:
            section_name = form_data["alias"]
            config.add_section(section_name)
            config.set(section_name, 'ip', form_data["ip"])
            config.set(section_name, 'password', form_data["password"])
            config.set(section_name, 'type', form_data["components"])

        # Writing our configuration file to 'example.cfg'
        with open(testbed_file, 'w') as configfile:
            config.write(configfile)

class TestcaseForm(forms.Form):
    class Rules:
        ABORT, ABORT_SECTION = "ABORT", "ABORT_SECTION"

    RULE_CHOICES = (
        (None , "-- Select a Failure Rule --"),
        (Rules.ABORT , "Abort"),
        (Rules.ABORT_SECTION , "Abort Section")
    )
    section = forms.CharField(label="Section", validators=[validate_no_spaces], required=False)
    script = forms.ChoiceField(label="Script")
    rule = forms.ChoiceField(choices=RULE_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super(TestcaseForm, self).__init__(*args, **kwargs)
        scripts = sorted(find_all_files(settings.POTLUCK.SCRIPTS_DIR, patterns=[".py$", "!__init__.py$", "!^lib/"]))
        # Special case: Process sikuli testcases to show the directory name
        scripts = map(_extract_sikuli_path, scripts)
        self.fields["script"].choices = _choices_to_groups(scripts, empty=True, empty_text="--- Choose a Script ---")
        if "initial" in kwargs:
            # Take care of the initial params now (Since we added choices afterwards)
            self.fields["script"].initial = kwargs["initial"]

class TestsuiteForm(forms.Form):
    name = forms.CharField(label="Testsuite Name", validators=[validate_no_spaces])

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.overwrite = kwargs.pop("overwrite", False)
        super(TestsuiteForm, self).__init__(*args, **kwargs)

    @property
    def path(self):
        if not hasattr(self, "_testsuite_path"):
            testsuite_name = self.cleaned_data["name"]
            # Make sure the testbed is created in the user's directory
            self._testsuite_path = os.path.join(settings.POTLUCK.USER_SUITES_DIR, self.user.username, testsuite_name)
        return self._testsuite_path
        
    def clean(self):
        cleaned_data = super(TestsuiteForm, self).clean()

        # Validate path existence only if a valid name was passed
        if "name" in cleaned_data and self.overwrite is not True and os.path.exists(self.path):
            raise forms.ValidationError("Testsuite already exists. Please choose a different name or go to edit page to modify the suite")

        return self.cleaned_data

class BaseTestsuiteFormset(BaseFormSet):
    def add_fields(self, form, index):
        super(BaseTestsuiteFormset, self).add_fields(form, index)
        form.fields['ORDER'].widget = forms.HiddenInput(attrs={"class" : "sort-position"})

    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        if self.total_form_count() <= 0:
            raise forms.ValidationError("Minimum one testcase selection is required")

    def create_file(self, testsuite_file):
        suite_tag = ET.Element("suite")
        default_section_tag = ET.SubElement(suite_tag, "section", attrib={"name" : "DEFAULT"})

        if not testsuite_file.lower().endswith(".xml"):
            testsuite_file += ".xml"

        testsuite_dir = os.path.dirname(testsuite_file)
        if not os.path.exists(testsuite_dir):
            os.makedirs(testsuite_dir)

        last_section = None
        for form in self.ordered_forms:
            form_data = form.cleaned_data
            script_name = form_data["script"]
            rule = form_data.get("rule")
            section_name = form_data.get("section", "").upper()

            logger.info("%s : %s" % (section_name, script_name))
            if section_name and section_name != last_section:
                section_tag = ET.SubElement(suite_tag, "section", attrib={"name" : section_name})
                last_section = section_name
            elif not section_name and last_section is None:
                # If this is the first script
                section_tag = default_section_tag

            testcase_tag = ET.SubElement(section_tag, "testcase")
            script_tag = ET.SubElement(testcase_tag, "script")
            script_tag.text = script_name
            if rule:
                rule_tag = ET.SubElement(testcase_tag, "onFailure")
                rule_tag.text = rule

        # If no script is present under default section, then remove the default section
        if len(default_section_tag) == 0:
            suite_tag.remove(default_section_tag)

        # Write out the suite file
        with open(testsuite_file, "w") as output_file:
            dom = xml.dom.minidom.parseString(ET.tostring(suite_tag))
            dom.writexml(output_file, addindent="    ", newl="\n")
