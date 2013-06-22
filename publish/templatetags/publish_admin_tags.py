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

# @register.inclusion_tag('admin/publish_submit_line.html', takes_context=True)
# def publish_submit_row(context):
#     """
#     Displays the row of buttons for delete and save.
#     """
#     opts = context['opts']
#     change = context['change']
#     is_popup = context['is_popup']
#     save_as = context['save_as']
#
#     ctx = {
#         'opts': opts,
#         'onclick_attrib': (opts.get_ordered_objects() and change
#                             and 'onclick="submitOrderForm();"' or ''),
#         'show_delete_link': (not is_popup and context['has_delete_permission']
#                               and change and context.get('show_delete', True)),
#         'show_save_as_new': not is_popup and change and save_as,
#         'show_save_and_add_another': context['has_add_permission'] and
#                             not is_popup and (not save_as or context['add']),
#         'show_save_and_continue': not is_popup and context['has_change_permission'],
#         'is_popup': is_popup,
#         'show_save': True
#     }
#     if context.get('original') is not None:
#         ctx['original'] = context['original']
#     return ctx
