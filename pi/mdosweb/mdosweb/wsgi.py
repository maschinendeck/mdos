"""
WSGI config for mdosweb project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import RPi.GPIO as GPIO
from time import sleep


# RELAY0
PIN_22 = 15

# RELAY1
PIN_23 = 16

GPIO.setmode(GPIO.BOARD)

GPIO.setup(PIN_22, GPIO.OUT)
GPIO.setup(PIN_23, GPIO.OUT)

GPIO.output(PIN_22, 1)
GPIO.output(PIN_23, 1)


from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mdosweb.settings")

application = get_wsgi_application()
