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

from collections import namedtuple
from datetime import datetime

from django.db import connection
from django.db.models import F

from backend.lk.models import Image
from backend.lk.models import ScreenshotSet
from backend.lk.models import ScreenshotShot
from backend.lk.models import ScreenshotShotOverride
from backend.lk.logic import gae_photos


#
# UPLOAD IMAGES
#

CreateImageResult = namedtuple('ImageAssignmentResult', ['server_error', 'bad_request', 'image'])

def create_screenshot_with_gae_id(gae_id, user=None):
  image = Image(kind='screenshot', user=user)
  # Need to get an ID.
  image.save()

  result = gae_photos.assign_upload_and_update_image(gae_id, image)
  if not result.success:
    image.delete()
    return CreateImageResult(result.server_error, result.bad_request, None)

  return CreateImageResult(False, False, image)


def create_background_with_gae_id(gae_id, user=None):
  image = Image(kind='background', user=user)
  # Need to get an ID.
  image.save()

  result = gae_photos.assign_upload_and_update_image(gae_id, image)
  if not result.success:
    image.delete()
    return CreateImageResult(result.server_error, result.bad_request, None)

  return CreateImageResult(False, False, image)


def create_website_icon_with_gae_id(gae_id, user=None):
  image = Image(kind='website-icon', user=user)
  # Need to get an ID.
  image.save()

  result = gae_photos.assign_upload_and_update_image(gae_id, image)
  if not result.success:
    image.delete()
    return CreateImageResult(result.server_error, result.bad_request, None)

  return CreateImageResult(False, False, image)


def create_website_background_with_gae_id(gae_id, user=None):
  image = Image(kind='website-background', user=user)
  # Need to get an ID.
  image.save()

  result = gae_photos.assign_upload_and_update_image(gae_id, image)
  if not result.success:
    image.delete()
    return CreateImageResult(result.server_error, result.bad_request, None)

  return CreateImageResult(False, False, image)


def create_website_logo_with_gae_id(gae_id, user=None):
  image = Image(kind='website-logo', user=user)
  # Need to get an ID.
  image.save()

  result = gae_photos.assign_upload_and_update_image(gae_id, image)
  if not result.success:
    image.delete()
    return CreateImageResult(result.server_error, result.bad_request, None)

  return CreateImageResult(False, False, image)


def create_website_screenshot_with_gae_id(gae_id, user=None):
  image = Image(kind='website-screenshot', user=user)
  # Need to get an ID.
  image.save()

  result = gae_photos.assign_upload_and_update_image(gae_id, image)
  if not result.success:
    image.delete()
    return CreateImageResult(result.server_error, result.bad_request, None)

  return CreateImageResult(False, False, image)


def assign_image_to_user(image, user):
  if image.user_id:
    if image.user_id != user.id:
      raise RuntimeError('Image already assigned to different user: %s (%s)' % (image.id, user.id))
    return

  image.user = user
  image.save(update_fields=['user'])


#
# CREATE AND MODIFY SETS
#


def get_my_sets(user):
  return ScreenshotSet.objects.filter(user=user, delete_time__isnull=True).order_by('-update_time')[:100]


def decorate_with_preview_images(my_sets, num_preview_images=2):
  if not my_sets:
    return

  sets_by_id = {s.id: s for s in my_sets}
  cursor = connection.cursor()
  cursor.execute("""
    WITH images_by_set_id AS (
      SELECT lk_image.id AS image_id, screenshot_set_id AS set_id, lk_screenshotshot.create_time AS create_time
      FROM lk_image INNER JOIN lk_screenshotshot ON lk_image.id = lk_screenshotshot.screenshot_image_id
      WHERE lk_screenshotshot.screenshot_set_id IN (%s)
      ORDER BY lk_screenshotshot.screenshot_set_id, lk_screenshotshot.create_time
    ),
    numbered_image_ids AS (
      SELECT image_id, set_id, ROW_NUMBER() OVER(PARTITION BY set_id ORDER BY create_time) AS row_num
      FROM images_by_set_id
    )
    SELECT image_id, set_id FROM numbered_image_ids WHERE row_num <= %%s
  """ % ','.join(['%s'] * len(sets_by_id)), sets_by_id.keys() + [num_preview_images])

  image_id_set_id = list(cursor.fetchall())
  image_ids = {image_id for image_id, _ in image_id_set_id}

  images = Image.objects.filter(id__in=list(image_ids))
  images_by_id = {i.id: i for i in images}

  for image_id, set_id in image_id_set_id:
    my_set = sets_by_id[set_id]
    if not my_set.decorated_images:
      my_set.decorated_images = []
    my_set.decorated_images.append(images_by_id[image_id])


def create_set(user, name, version, platform):
  new_set = ScreenshotSet(user=user, name=name, version=version, shot_count=0)
  new_set.platform = platform
  new_set.save()
  return new_set

def update_set(my_set, name=None, version=None):
  if name:
    my_set.name = name
  if version:
    my_set.version = version
  my_set.save()


def duplicate_set(my_set, new_name, new_version, platform):
  new_set = ScreenshotSet(user=my_set.user, name=new_name, version=new_version, shot_count=my_set.shot_count)
  new_set.platform = platform
  new_set.save()

  referenced_image_ids = {}
  def ref_image(image_id):
    if image_id not in referenced_image_ids:
      referenced_image_ids[image_id] = 0
    referenced_image_ids[image_id] += 1

  shots = list(
    ScreenshotShot.objects
      .filter(screenshot_set_id=my_set.id)
      .select_related('screenshot_image', 'background_image')
      .order_by('id')
  )

  for shot in shots:
    new_shot = ScreenshotShot(user=my_set.user, screenshot_set=new_set)
    new_shot.config = shot.config

    # android phones only have one color, set to black incase the set being cloned is iOS w/ a different color phone
    if platform == 'Android':
      new_shot.phone_color = 'black'

    if shot.screenshot_image_id:
      new_shot.screenshot_image_id = shot.screenshot_image_id
      ref_image(shot.screenshot_image_id)
    if shot.background_image_id:
      new_shot.background_image_id = shot.background_image_id
      ref_image(shot.background_image_id)

    new_shot.save()

    # only duplicate shot overrides if the platform is the same as the old set
    if platform == my_set.platform:
      # filter shot overrides
      overrides = ScreenshotShotOverride.objects.filter(screenshot_set_id=my_set.id, screenshot_shot_id=shot.id).select_related('override_image')

      for override in overrides:
        #create new overrides for new set + new shots
        new_override = ScreenshotShotOverride(
          screenshot_set_id=new_set.id,
          screenshot_shot_id=new_shot.id,
          device_type=override.device_type,
          override_image_id=override.override_image.id,
          data=override.data)
        new_override.save()

        # increment ref_counts
        ref_image(override.override_image_id)

  increments_ids = {}
  for image_id, increment in referenced_image_ids.items():
    if increment not in increments_ids:
      increments_ids[increment] = []
    increments_ids[increment].append(image_id)
  for increment, image_ids in increments_ids.items():
    Image.objects.filter(id__in=image_ids).update(ref_count=F('ref_count') + increment)

  return new_set



def get_set_and_shots_by_encrypted_id(user, encrypted_id, enable_logged_out=False):
  my_set = get_set_by_encrypted_id(user, encrypted_id, enable_logged_out=enable_logged_out)
  if not my_set:
    return None, None

  shots = ScreenshotShot.objects.filter(screenshot_set_id=my_set.id).order_by('id')
  return my_set, shots


def get_set_by_encrypted_id(user, encrypted_id, enable_logged_out=False):
  my_set = ScreenshotSet.find_by_encrypted_id(encrypted_id)
  user_matches = enable_logged_out or (my_set and my_set.user_id == user.id)
  if not my_set or not user_matches or my_set.delete_time:
    return None
  return my_set


def delete_my_set(user, my_set):
  if my_set.user_id != user.id:
    raise RuntimeError('Set does not belong to this user')

  my_set.delete_time = datetime.now()
  my_set.save(update_fields=['delete_time'])


#
# CREATE AND MODIFY SHOTS
#


def update_shot_with_fields(shot, **fields):
  if 'screenshot_image' in fields:
    screenshot_image = fields['screenshot_image']
    del fields['screenshot_image']

    if shot.screenshot_image_id:
      Image.objects.filter(id=shot.screenshot_image_id).update(ref_count=F('ref_count') - 1)
    if screenshot_image:
      Image.objects.filter(id=screenshot_image.id).update(ref_count=F('ref_count') + 1)
      screenshot_image.ref_count += 1
    shot.screenshot_image = screenshot_image

  if 'background_image' in fields:
    background_image = fields['background_image']
    del fields['background_image']

    if shot.background_image_id:
      Image.objects.filter(id=shot.background_image_id).update(ref_count=F('ref_count') - 1)
    if background_image:
      Image.objects.filter(id=background_image.id).update(ref_count=F('ref_count') + 1)
      background_image.ref_count += 1
    shot.background_image = background_image

  if 'label' in fields:
    shot.label = fields['label']
    del fields['label']
  else:
    shot.label = ''

  if 'label_position' in fields:
    shot.label_position = fields['label_position']
    del fields['label_position']

  if 'font' in fields:
    shot.font = fields['font']
    del fields['font']

  if 'font_size' in fields:
    shot.font_size = fields['font_size']
    del fields['font_size']

  if 'font_weight' in fields:
    shot.font_weight = fields['font_weight']
    del fields['font_weight']

  if 'font_color' in fields:
    shot.font_color = fields['font_color']
    del fields['font_color']

  if 'phone_color' in fields:
    shot.phone_color = fields['phone_color']
    del fields['phone_color']

  if 'background_color' in fields:
    shot.background_color = fields['background_color']
    del fields['background_color']

  if 'is_landscape' in fields:
    shot.is_landscape = fields['is_landscape']
    del fields['is_landscape']

  if fields:
    raise RuntimeError('Unknown shot update field(s): %s' % (fields.keys()))


def create_shot_in_set(user, my_set, **fields):
  shot = ScreenshotShot(user=user, screenshot_set=my_set)
  update_shot_with_fields(shot, **fields)
  shot.save()

  ScreenshotSet.objects.filter(id=my_set.id).update(shot_count=F('shot_count') + 1, update_time=datetime.now())
  return shot


def update_shot(my_shot, **fields):
  update_shot_with_fields(my_shot, **fields)
  my_shot.save()


def delete_shot_in_set(my_set, shot):
  image_ids = filter(lambda x: x, [shot.screenshot_image_id, shot.background_image_id])

  # filter override images for this shot to update ref_count's
  image_ids += list(
    ScreenshotShotOverride.objects
      .filter(screenshot_set=my_set, screenshot_shot=shot)
      .values_list('override_image', flat=True)
      .distinct()
  )

  if image_ids:
    Image.objects.filter(id__in=image_ids).update(ref_count=F('ref_count') - 1)

  # delete any overrides
  ScreenshotShotOverride.objects.filter(screenshot_shot=shot).delete()

  shot.delete()
  ScreenshotSet.objects.filter(id=my_set.id).update(shot_count=F('shot_count') - 1, update_time=datetime.now())


#
# SHOT OVERRIDES BT DEVICE_TYPE
#


def get_shot_and_override_image_by_encrypted_id(user, shot_id, image_id):
  my_shot = ScreenshotShot.find_by_encrypted_id(shot_id)
  image = Image.find_by_encrypted_id(image_id)
  user_matches = (my_shot and my_shot.user_id == user.id) and (image and image.user_id == user.id)

  if not my_shot or not image or not user_matches:
    return None, None

  return my_shot, image

def get_shot_override_by_encrypted_id(user, shot_id, device_type):
  my_shot = ScreenshotShot.find_by_encrypted_id(shot_id)
  override = ScreenshotShotOverride.objects.filter(screenshot_shot=my_shot, device_type=device_type).first()
  user_matches = (my_shot and my_shot.user_id == user.id)

  if not override or not user_matches:
    return None

  return override

def create_or_update_override_image(shot_set, my_shot, image, device_type):
  # Determine the orientation
  # Todo implement this at a higher level for screenshots
  if image.width > image.height:
    is_landscape = True
  else:
    is_landscape = False

  override_image_qs = ScreenshotShotOverride.objects.filter(screenshot_set=shot_set, screenshot_shot=my_shot, device_type=device_type)

  image.to_qs().update(ref_count=F('ref_count') + 1)

  old_override = override_image_qs.first()
  if old_override:
    # grab the old image object to delete it
    old_override_image = old_override.override_image

    # set the old image ref_count to 0 for cleanup
    old_override_image.to_qs().update(ref_count=F('ref_count') - 1)

    # replace the old override image with the new one
    override_image_qs.update(override_image=image, update_time=datetime.now())
    new_override = override_image_qs.first()
    new_override.is_landscape = is_landscape
    new_override.save()

  else:
    # override doesnt exist, create a new one
    new_override = ScreenshotShotOverride(screenshot_set=shot_set, screenshot_shot=my_shot, override_image=image, device_type=device_type)
    new_override.is_landscape = is_landscape
    new_override.save()

  #return the override
  return new_override

def delete_override_image(override):
  #subtract ref_count on override_image for cleanup
  override.override_image.to_qs().update(ref_count=F('ref_count') - 1)
  # delete the override object
  override.delete()

  return True

