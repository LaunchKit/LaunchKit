
from django.db import models

from backend.lk.models.apimodel import APIModel
from backend.lk.models.users import User
from backend.lk.models.sdksession import SDKSession
from backend.lk.models.sdkuser import SDKUser


class SDKVisit(APIModel):
  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  session = models.ForeignKey(SDKSession, related_name='+', on_delete=models.DO_NOTHING)
  sdk_user = models.ForeignKey(SDKUser, related_name='+', null=True, on_delete=models.DO_NOTHING)

  os = models.CharField(max_length=3, null=True)
  os_version = models.CharField(max_length=16, null=True)
  hardware = models.CharField(max_length=32, null=True)

  app_version = models.CharField(max_length=32, null=True)
  app_build = models.CharField(max_length=32, null=True)
  app_build_debug = models.NullBooleanField(null=True)

  screen_height = models.PositiveIntegerField(null=True)
  screen_width = models.PositiveIntegerField(null=True)
  screen_scale = models.FloatField(null=True)

  start_time = models.DateTimeField()
  end_time = models.DateTimeField()

  screens = models.PositiveIntegerField()
  taps = models.PositiveIntegerField()

  def to_dict(self):
    if self.os:
      os_version = '%s %s' % (self.os, self.os_version)
    else:
      os_version = None

    if self.hardware:
      hardware = self.hardware
    else:
      hardware = None

    if self.app_version:
      if self.app_build:
        if self.app_build_debug:
          app_version = '%s (%s - DEBUG)' % (self.app_version, self.app_build)
        else:
          app_version = '%s (%s)' % (self.app_version, self.app_build)
      else:
        app_version = self.app_version

    else:
      app_version = None

    visit = {
      'startTime': self.date_to_api_date(self.start_time),
      'endTime': self.date_to_api_date(self.end_time),
      'seconds': (self.end_time - self.start_time).total_seconds(),

      'device': {
        'os': os_version,
        'hardware': hardware,
      },
      'app': {
        'version': app_version,
      },

      'screens': self.screens,
      'taps': self.taps,
    }

    if self.sdk_user_id:
      visit['userId'] = SDKUser.encrypt_id(self.sdk_user_id)

    return visit
