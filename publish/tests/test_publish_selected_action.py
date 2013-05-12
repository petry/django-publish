from django.conf import settings
from django.conf.urls import patterns, include
from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from publish.actions import publish_selected, _convert_all_published_to_html
from publish.admin import PublishableAdmin
from publish.tests.example_app.models import Page, PageBlock, Author
from publish.utils import NestedSet

__author__ = 'petry'


class TestPublishSelectedAction(TestCase):

    def setUp(self):
        super(TestPublishSelectedAction, self).setUp()
        self.fp1 = Page.objects.create(slug='fp1', title='FP1')
        self.fp2 = Page.objects.create(slug='fp2', title='FP2')
        self.fp3 = Page.objects.create(slug='fp3', title='FP3')

        self.admin_site = AdminSite('Test Admin')
        self.page_admin = PublishableAdmin(Page, self.admin_site)

        # override urls, so reverse works
        settings.ROOT_URLCONF=patterns('',
            ('^admin/', include(self.admin_site.urls)),
        )

    def test_publish_selected_confirm(self):
        pages = Page.objects.exclude(id=self.fp3.id)

        class dummy_request(object):
            META = {}
            POST = {}

            class user(object):
                @classmethod
                def has_perm(cls, *arg):
                    return True

                @classmethod
                def get_and_delete_messages(cls):
                    return []

        response = publish_selected(self.page_admin, dummy_request, pages)

        self.failIf(Page.objects.published().count() > 0)
        self.failUnless(response is not None)
        self.failUnlessEqual(200, response.status_code)

    def test_publish_selected_confirmed(self):
        pages = Page.objects.exclude(id=self.fp3.id)

        class dummy_request(object):
            POST = {'post': True}

            class user(object):
                @classmethod
                def is_authenticated(cls):
                    return True

                @classmethod
                def has_perm(cls, *arg):
                    return True

                class message_set(object):
                    @classmethod
                    def create(cls, message=None):
                        self._message = message

            class _messages(object):
                @classmethod
                def add(cls, *message):
                    self._message = message


        response = publish_selected(self.page_admin, dummy_request, pages)


        self.failUnlessEqual(2, Page.objects.published().count())
        self.failUnless( getattr(self, '_message', None) is not None )
        self.failUnless( response is None )

    def test_convert_all_published_to_html(self):
        self.admin_site.register(Page, PublishableAdmin)

        all_published = NestedSet()

        page = Page.objects.create(slug='here', title='title')
        block = PageBlock.objects.create(page=page, content='stuff here')

        all_published.add(page)
        all_published.add(block, parent=page)

        converted = _convert_all_published_to_html(self.admin_site, all_published)

        expected = [u'<a href="../../example_app/page/%d/">Page: here (Changed - not yet published)</a>' % page.id, [u'Page block: PageBlock object']]

        self.failUnlessEqual(expected, converted)

    def test_publish_selected_does_not_have_permission(self):
        self.admin_site.register(Page, PublishableAdmin)
        pages = Page.objects.exclude(id=self.fp3.id)

        class dummy_request(object):
            POST = {}
            META = {}

            class user(object):
                @classmethod
                def has_perm(cls, *arg):
                    return False

                @classmethod
                def get_and_delete_messages(cls):
                    return []

        response = publish_selected(self.page_admin, dummy_request, pages)
        self.failIf(response is None)
        # publish button should not be in response
        self.failIf('value="publish_selected"' in response.content)
        self.failIf('value="Yes, Publish"' in response.content)
        self.failIf('form' in response.content)

        self.failIf(Page.objects.published().count() > 0)

    def test_publish_selected_does_not_have_related_permission(self):
        # check we can't publish when we don't have permission
        # for a related model (in this case authors)
        self.admin_site.register(Author, PublishableAdmin)

        author = Author.objects.create(name='John')
        self.fp1.authors.add(author)

        pages = Page.objects.draft()

        class dummy_request(object):
            POST = { 'post': True }

            class _messages(object):
                @classmethod
                def add(cls, *args):
                    return 'message'

            class user(object):
                pk = 1

                @classmethod
                def is_authenticated(cls):
                    return True

                @classmethod
                def has_perm(cls, perm):
                    return perm != 'example_app.publish_author'

        try:
            publish_selected(self.page_admin, dummy_request, pages)

            self.fail()
        except PermissionDenied:
            pass

        self.failIf(Page.objects.published().count() > 0)

    def test_publish_selected_logs_publication(self):
        self.admin_site.register(Page, PublishableAdmin)

        pages = Page.objects.exclude(id=self.fp3.id)

        class dummy_request(object):
            POST = { 'post': True }

            class user(object):
                pk = 1

                @classmethod
                def is_authenticated(cls):
                    return True

                @classmethod
                def has_perm(cls, perm):
                    return perm != 'example_app.publish_author'

                class message_set(object):
                    @classmethod
                    def create(cls, message=None):
                        pass

            class _messages(object):
                @classmethod
                def add(cls, *message):
                    pass

        publish_selected(self.page_admin, dummy_request, pages)

        # should have logged two publications
        from django.contrib.admin.models import LogEntry
        from django.contrib.contenttypes.models import ContentType

        content_type_id = ContentType.objects.get_for_model(self.fp1).pk
        self.failUnlessEqual(2, LogEntry.objects.filter().count())