
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')


#
# NOTE: Do this here, instead of settings, because if you do it from settings
# it loads settings and causes a subtle settings import loop.
#

from django.template.base import add_to_builtins

# Add template tags to all templates for {% static %} directive.
add_to_builtins('django.contrib.staticfiles.templatetags.staticfiles')


# Get celery loaded here.
from backend.celery_app import celery_app
