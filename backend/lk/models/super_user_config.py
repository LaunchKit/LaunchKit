#
# Copyright 2016 Cluster Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from backend.util import enum


class ActiveStatus(enum.Enum):
  MonthlyActive = 'active-1m'
  WeeklyActive = 'active-1w'
  MonthlyInactive = 'inactive-1m'
  WeeklyInactive = 'inactive-1w'


class SessionFrequency(enum.Enum):
  MoreThanOnceADay = 'Mvpd'
  OnceADay = '1vpd'
  FiveDaysAWeek = '5vpw'
  ThreeDaysAWeek = '3vpw'
  OnceAWeek = '1vpw'
  TwiceAMonth = '2vpm'

  # Remove from "super" choices because we don't want users to choose this as super.
  @classmethod
  def choices(cls):
    choices = super(SessionFrequency, cls).choices()
    return [(c, l) for c, l in choices if c != SessionFrequency.TwiceAMonth]


SESSION_FREQUENCY_ORDER = (
  SessionFrequency.MoreThanOnceADay,
  SessionFrequency.OnceADay,
  SessionFrequency.FiveDaysAWeek,
  SessionFrequency.ThreeDaysAWeek,
  SessionFrequency.OnceAWeek,
  SessionFrequency.TwiceAMonth,
)


class CumulativeTimeUsed(enum.Enum):
  HourPerDay = '1hpd'
  FifteenMinutesPerDay = '15mpd'
  FiveMinutesPerDay = '5mpd'
  OneMinutePerDay = '1mpd'
  ThirtySecondsPerDay = '30spd'

  # Remove from "super" choices because we don't want users to choose this as super.
  @classmethod
  def choices(cls):
    choices = super(CumulativeTimeUsed, cls).choices()
    return [(c, l) for c, l in choices if c != CumulativeTimeUsed.ThirtySecondsPerDay]


CUMULATIVE_TIME_ORDER = (
  CumulativeTimeUsed.HourPerDay,
  CumulativeTimeUsed.FifteenMinutesPerDay,
  CumulativeTimeUsed.FiveMinutesPerDay,
  CumulativeTimeUsed.OneMinutePerDay,
  CumulativeTimeUsed.ThirtySecondsPerDay,
)


DEFAULT_SUPER_CONFIG_FREQ = SessionFrequency.FiveDaysAWeek
DEFAULT_SUPER_CONFIG_TIME = CumulativeTimeUsed.FiveMinutesPerDay

DEFAULT_ALMOST_CONFIG_FREQ = SessionFrequency.ThreeDaysAWeek
DEFAULT_ALMOST_CONFIG_TIME = CumulativeTimeUsed.OneMinutePerDay

ALL_USER_LABELS = (
    ['super', 'fringe'] +
    list(ActiveStatus.kinds())  +
    list(SessionFrequency.kinds()) +
    list(CumulativeTimeUsed.kinds())
)
