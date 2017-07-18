# Django settings for web project.
import os
import sys

WEB_APP_DIR = os.path.abspath(os.path.dirname(__file__))
WEB_DIR = os.path.dirname(WEB_APP_DIR)
SRC_DIR = os.path.dirname(WEB_DIR)
WEB_MODULES_DIR = os.path.join(WEB_DIR, "modules")
WEB_MODULES_ZIP = os.path.join(WEB_DIR, "modules.zip")

sys.path.insert(0, WEB_MODULES_ZIP)
sys.path.insert(0, WEB_MODULES_DIR)
sys.path.insert(0, SRC_DIR)

# Include potluck settings
POTLUCK_SETTINGS_FILE = os.path.join(SRC_DIR, "settings.py")
import imp
POTLUCK = imp.load_source("POTLUCK", POTLUCK_SETTINGS_FILE)

DEBUG = os.environ.get("POTLUCK_DEBUG") == "1"
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Tarun', 'tarun.batra@guavus.com'),
)

MANAGERS = ADMINS

DATABASES = {
}

DATABASES_ = {
    'sqllite': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(WEB_DIR, "potluck.db"),                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    },
    'mysql': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': "potluck",
        'USER': 'root',
        'PASSWORD': 't00lk1t',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

if DEBUG is False:
    DATABASES["default"] = DATABASES_["mysql"]
else:
    DATABASES["default"] = DATABASES_["sqllite"]

WEB_LOGS_DIR = "/var/log/potluck"
if not os.path.exists(WEB_LOGS_DIR):
    try:
        os.makedirs(WEB_LOGS_DIR)
    except Exception as e:
        sys.stdout.write("Unable to write logs at %s. Trying for %s\n" % (WEB_LOGS_DIR, POTLUCK.LOGS_DIR))
        WEB_LOGS_DIR = POTLUCK.LOGS_DIR
        if not os.path.exists(WEB_LOGS_DIR):
            os.makedirs(WEB_LOGS_DIR)

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["127.0.0.1", "192.168.117.124"]

SITE_ID = 1

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(WEB_DIR, "static")

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    WEB_APP_DIR + "/static",
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'h48w+#dbvcdx9zs7!6on_!%n9x6a!pu*x(#uvi9d9!goo!l)h^'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (                                         
    'django.core.context_processors.request',
    "django.contrib.auth.context_processors.auth",                  
    "django.core.context_processors.debug",                         
    "django.core.context_processors.i18n",                          
    "django.core.context_processors.media",                         
    "django.core.context_processors.static",                        
    "django.core.context_processors.tz",                            
    "django.contrib.messages.context_processors.messages"           
)      

AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = 'web.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'web.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    WEB_APP_DIR + "/templates",
)

INSTALLED_APPS = (
    'django.core',  # Workaround to load core's management commands
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_admin_bootstrapped.bootstrap3',
    'django_admin_bootstrapped',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',

    'home',
    'accounts',
    'bootstrap3',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
WEB_LOG_FILE = os.path.join(WEB_LOGS_DIR, 'potluck.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s %(levelname)s] %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': WEB_LOG_FILE,
            'maxBytes' : 10000000,
            'backupCount' : 5,
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'home': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'home.management': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django_auth_ldap': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'utils': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        }
    }
}

if DEBUG is True:
    for logger in LOGGING["loggers"]:
        LOGGING["loggers"][logger]["handlers"].append("console")

# Provide permissions to other users
try:
    os.chmod(WEB_LOGS_DIR, 0o777)
except Exception as e:
    #sys.stderr.write(str(e))
    pass

try:
    os.chmod(WEB_LOG_FILE, 0o777)
except Exception as e:
    #sys.stderr.write(str(e))
    pass

# bootstrap3 settings
BOOTSTRAP3 = {
    'jquery_url': STATIC_URL + 'js/jquery.min.js',
    'base_url': STATIC_URL,
}

# LDAP Config
#AUTH_LDAP_SERVER_URI = "ldap://mx1.guavus.com"
AUTH_LDAP_SERVER_URI = "ldap://103.14.2.35"
AUTH_LDAP_USER_DN_TEMPLATE = "%(user)s@guavus.com"
AUTH_LDAP_USER_ATTR_MAP = {"first_name": "givenName", "last_name": "sn", "email" : "mail"}

# Account URLs
LOGIN_URL = "login"
LOGOUT_URL = "logout"
LOGIN_REDIRECT_URL = "home"
