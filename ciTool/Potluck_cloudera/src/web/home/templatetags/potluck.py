from django import template
from django.conf import settings
from django.core.urlresolvers import reverse

import os
import re
import random

# Django template library
register = template.Library()

scripts_dir = settings.POTLUCK.SCRIPTS_DIR

@register.filter
def docs_path(value):
    docs_url_prefix = "/docs/testcases"
    script_docs = re.sub(scripts_dir, docs_url_prefix, value)
    return os.path.splitext(script_docs)[0] + ".html"

@register.simple_tag
def random_404():
    return random.choice([
        "I Wish God Was Here",
        "Try Wikipedia Instead"
    ])

@register.filter
def multiply(value, arg):
    return value * arg

class IncrementVarNode(template.Node):
    def __init__(self, var_name, incr_by=1):
        self.var_name = var_name
        self.incr_by = incr_by

    def render(self,context):
        if self.var_name not in context:
            value = 1
        else:
            value = context[self.var_name]
        context[self.var_name] = int(value) + int(self.incr_by)
        return u""

@register.simple_tag(takes_context=True)
def incr(context, variable, incr_by=1):
    if variable not in context:
        value = 0
    else:
        value = context[variable]
    context[variable] = int(value) + int(incr_by)
    return ""

def increment_var2(parser, token):
    parts = token.split_contents()
    parts_length = len(parts)
    if parts_length < 2 or parts_length > 3:
        raise template.TemplateSyntaxError("'increment' tag must be of the form:  {% increment <var_name> [<value>] %}")
    return IncrementVarNode(*parts[1:])
