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

from datetime import datetime

# Example EXIF data:
#
# Nikon D40:
# {u'YResolution': 300, u'LightSource': 0, u'ResolutionUnit': 2, u'Make': u'NIKON CORPORATION',
#  u'Flash': 0, u'SceneCaptureType': 0,
#  u'DateTime': u'2009:06:14 12:54:21', u'MaxApertureValue': 4.5, u'MeteringMode': 5, u'XResolution': 300,
#  u'ExposureBiasValue': -1.3333334, u'MimeType': 0, u'Saturation': 0, u'ColorProfile': False,
#  u'ExposureProgram': 2, u'FocalLengthIn35mmFilm': 150, u'ColorSpace': 1,
#  u'Lens': u'AF-S DX Zoom-Nikkor 55-200mm f/4-5.6G ED', u'Contrast': 0,
#  u'DateTimeOriginal': u'1244984061', u'ImageWidth': 3008, u'SubsecTime': u'50',
#  u'SubjectDistanceRange': 0, u'WhiteBalance': 0, u'CompressedBitsPerPixel': 4,
#  u'DateTimeDigitized': u'2009:06:14 12:54:21', u'SensingMethod': 2, u'FNumber': 11,
#  u'CustomRendered': 0, u'FocalLength': 100, u'SubsecTimeOriginal': u'50', u'ExposureMode': 0,
#  u'SubsecTimeDigitized': u'50', u'ISOSpeedRatings': 400, u'Model': u'NIKON D40',
#  u'InteroperabilityIndex': u'R98', u'Software': u'Ver.1.11 ', u'ExposureTime': 0.00062499999,
#  u'ImageLength': 2000, u'Orientation': 1, u'Sharpness': 0, u'DateCreated': u'2009:06:14 12:54:21',
#  u'CCDWidth': 23.700001, u'GainControl': 1, u'YCbCrPositioning': 2, u'DigitalZoomRatio': 1},
#
# iPhone 5:
# {u'YResolution': 72, u'GPSImgDirectionRef': u'T', u'ResolutionUnit': 2, u'GPSLongitude': -122.4185,
#  u'Make': u'Apple', u'Flash': 0, u'SceneCaptureType': 0, u'DateTime': u'2013:04:09 10:54:08',
#  u'SubjectArea': 1631, u'MeteringMode': 5, u'XResolution': 72, u'MimeType': 0, u'GPSImgDirection': 20.497406,
#  u'ColorProfile': False, u'ExposureProgram': 2, u'FocalLengthIn35mmFilm': 33, u'ShutterSpeedValue': 9.1716805,
#  u'ColorSpace': 1, u'DateTimeDigitized': u'2013:04:09 10:54:08', u'DateTimeOriginal': u'1365504848',
#  u'ImageWidth': 3264, u'BrightnessValue': 8.3673801, u'WhiteBalance': 0, u'SensingMethod': 2, u'FNumber': 2.4000001,
#  u'ApertureValue': 2.5260689, u'FocalLength': 4.1300001, u'ExposureMode': 0, u'GPSAltitude': 22.317139001349528,
#  u'GPSTimeStamp': 17, u'ISOSpeedRatings': 50, u'Model': u'iPhone 5', u'Software': u'6.1.3',
#  u'ExposureTime': 0.0017331023, u'ImageLength': 2448, u'Orientation': 1, u'DateCreated': u'2013:04:09 10:54:08',
#  u'GPSLatitude': 37.7555, u'YCbCrPositioning': 1}
#
# Old Olympus:
# {u'YResolution': 72, u'LightSource': 0, u'ResolutionUnit': 2, u'Make': u'OLYMPUS IMAGING CORP.  ',
#  u'Flash': 1, u'SceneCaptureType': 0, u'DateTime': u'2007:07:31 03:28:17', u'MaxApertureValue': 3.26,
#  u'MeteringMode': 5, u'XResolution': 72, u'ExposureBiasValue': 0, u'MimeType': 0, u'Saturation': 0,
#  u'ColorProfile': False, u'ExposureProgram': 5, u'ColorSpace': 1, u'Contrast': 0, u'DateTimeOriginal': u'1185852497',
#  u'ImageWidth': 2048, u'WhiteBalance': 0, u'CompressedBitsPerPixel': 2, u'DateTimeDigitized': u'2007:07:31 03:28:17',
#  u'FNumber': 3.0999999, u'CustomRendered': 0, u'FocalLength': 6.3000002, u'ExposureMode': 0, u'ISOSpeedRatings': 400,
#  u'Model': u'FE230/X790             ', u'Software': u'Version 1.0                    ', u'ExposureTime': 0.0040000002,
#  u'ImageLength': 1536, u'Orientation': 6, u'Sharpness': 0, u'DateCreated': u'2007:07:31 03:28:17', u'GainControl': 2,
#  u'DigitalZoomRatio': 0}
#
# Old Sony:
# {u'YResolution': 72, u'LightSource': 0, u'ResolutionUnit': 2, u'Make': u'SONY', u'Flash': 1,
#  u'DateTime': u'2004:10:30 21:35:35', u'MeteringMode': 5, u'XResolution': 72, u'ExposureBiasValue': 0,
#  u'MimeType': 0, u'ColorProfile': False, u'ExposureProgram': 2, u'FocalLengthIn35mmFilm': 38, u'ColorSpace': 1,
#  u'DateTimeDigitized': u'2004:10:30 21:35:35', u'DateTimeOriginal': u'1099172135', u'ImageWidth': 1536,
#  u'CompressedBitsPerPixel': 4, u'FNumber': 2.8, u'FocalLength': 7.9000001, u'ISOSpeedRatings': 160,
#  u'Model': u'DSC-P10', u'ExposureTime': 0.025, u'ImageLength': 2048, u'MaxApertureValue': 3,
#  u'DateCreated': u'2004:10:30 21:35:35', u'CCDWidth': 7.1440001, u'YCbCrPositioning': 2}
#


class ParsedExif(object):
  photo_time = None
  orientation = None

  latitude = None
  longitude = None

  def orientation_is_sideways(self):
    # 5, 6, 7, 8 are all sideways.
    return self.orientation and self.orientation > 4

  def has_location(self):
    return self.latitude is not None and self.longitude is not None

def parse_from_dict(exif_dict):
  parsed = ParsedExif()

  #
  # PARSE ORIENTATION
  #
  parsed.orientation = 1
  if 'Orientation' in exif_dict:
    try:
      parsed.orientation = int(exif_dict['Orientation'])
    except ValueError:
      pass

  #
  # PARSE TIME
  #

  photo_time = None
  unix_timestamp_fields = ['DateTimeOriginal',]
  for field in unix_timestamp_fields:
    if field not in exif_dict:
      continue

    maybe_timestamp = exif_dict[field]
    try:
      timestamp = long(maybe_timestamp)
    except ValueError, TypeError:
      continue

    try:
      photo_time = datetime.utcfromtimestamp(timestamp)
    except ValueError:
      continue

  date_time_fields = ['DateTimeDigitized', 'DateCreated',]
  if not photo_time:
    for field in date_time_fields:
      if field not in exif_dict:
        continue

      datetime_string = str(exif_dict[field])
      try:
        photo_time = datetime.strptime(datetime_string, '%Y:%m:%d %H:%M:%S')
      except ValueError:
        continue

  parsed.photo_time = photo_time

  #
  # PARSE LOCATION
  #

  if 'GPSLatitude' in exif_dict:
    try:
      latitude = float(exif_dict['GPSLatitude'])
      if -90 <= latitude <= 90:
        parsed.latitude = latitude
    except ValueError, TypeError:
      pass

  if 'GPSLongitude' in exif_dict:
    try:
      longitude = float(exif_dict['GPSLongitude'])
      if -180.0 <= longitude <= 180.0:
        parsed.longitude = longitude
    except ValueError, TypeError:
      pass

  return parsed
