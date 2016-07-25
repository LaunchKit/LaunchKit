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

from django.views.generic.base import TemplateView
from django.views.generic.base import RedirectView


class TextTemplateView(TemplateView):
    def render_to_response(self, context, **response_kwargs):
        response_kwargs['content_type'] = 'text/plain'
        return super(TextTemplateView, self).render_to_response(context, **response_kwargs)


class ContextualTemplateView(TemplateView):
    extra_context = None
    def get_context_data(self, **kwargs):
        kwargs.update(self.extra_context)
        return kwargs


def text_template_view(filename):
  # pylint: disable=E1120
  return TextTemplateView.as_view(template_name=filename)


def template_view(template_name, **context):
  # pylint: disable=E1120
  return ContextualTemplateView.as_view(template_name=template_name, extra_context=context)


def redirect_view(url):
  # pylint: disable=E1120
  return RedirectView.as_view(url=url)

