#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django import template
from django.contrib.admin.templatetags.admin_modify import submit_row

register = template.Library()


@register.inclusion_tag('admin/publish_submit_line.html', takes_context=True)
def publish_submit_row(context):
    ctx = submit_row(context)
    ctx['show_publish'] = context.get('has_publish_permission') \
        and context.get('change')

    return ctx
