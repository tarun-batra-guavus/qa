from django.shortcuts import redirect
from django.contrib.auth.views import login as django_login

def login(request, *args, **kwargs):
    if request.user.is_authenticated() and not request.REQUEST.get("next"):
        return redirect("home")

    if request.method == 'POST':
        if not request.POST.get('remember', None):
            request.session.set_expiry(0)
    return django_login(request, *args, **kwargs)
