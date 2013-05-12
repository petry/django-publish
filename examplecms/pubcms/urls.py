from django.conf.urls import patterns, url

from pubcms.views import page_detail
from pubcms.models import Page

urlpatterns = patterns(
    '',
    url('^(?P<page_url>.*)\*$', page_detail,
        {'queryset': Page.objects.draft()},
        name='draft_page_detail'),
    url('^(?P<page_url>.*)$', page_detail,
        {'queryset': Page.objects.published()},
        name='public_page_detail'),
)
