from django.conf import settings
from django.conf.urls import patterns, include
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.forms import ModelChoiceField, ModelMultipleChoiceField
from django.http import Http404
from django.test import TestCase, RequestFactory
from publish.admin import PublishableStackedInline, PublishableAdmin
from publish.models import Publishable
from publish.tests.example_app.models import Page, Author, PageBlock
from publish.tests.helpers import _get_rendered_content


class TestPublishableAdmin(TestCase):
    def setUp(self):
        super(TestPublishableAdmin, self).setUp()
        self.page1 = Page.objects.create(slug='page1', title='page 1')
        self.page2 = Page.objects.create(slug='page2', title='page 2')
        self.page1.publish()
        self.page2.publish()

        self.author1 = Author.objects.create(name='a1')
        self.author2 = Author.objects.create(name='a2')
        self.author1.publish()
        self.author2.publish()

        self.admin_site = AdminSite('Test Admin')

        class PageBlockInline(PublishableStackedInline):
            model = PageBlock

        class PageAdmin(PublishableAdmin):
            inlines = [PageBlockInline]

        self.admin_site.register(Page, PageAdmin)
        self.page_admin = PageAdmin(Page, self.admin_site)

        # override urls, so reverse works
        settings.ROOT_URLCONF = patterns(
            '',
            ('^admin/',
             include(self.admin_site.urls)),
        )

    def test_get_publish_status_display(self):
        page = Page.objects.create(slug="hhkkk", title="hjkhjkh")
        self.failUnlessEqual('Changed - not yet published',
                             self.page_admin.get_publish_status_display(page))
        page.publish()
        self.failUnlessEqual('Published',
                             self.page_admin.get_publish_status_display(page))
        page.save()
        self.failUnlessEqual('Changed',
                             self.page_admin.get_publish_status_display(page))

        page.delete()
        self.failUnlessEqual('To be deleted',
                             self.page_admin.get_publish_status_display(page))

    def test_queryset(self):
        # make sure we only get back draft objects
        request = None

        self.failUnlessEqual(
            set([self.page1, self.page1.public, self.page2,
                 self.page2.public]),
            set(Page.objects.all())
        )
        self.failUnlessEqual(
            set([self.page1, self.page2]),
            set(self.page_admin.queryset(request))
        )

    def test_get_actions_global_delete_replaced(self):
        from publish.actions import delete_selected

        class request(object):
            GET = {}

        actions = self.page_admin.get_actions(request)

        self.failUnless('delete_selected' in actions)
        action, name, description = actions['delete_selected']
        self.failUnlessEqual(delete_selected, action)
        self.failUnlessEqual('delete_selected', name)
        self.failUnlessEqual(delete_selected.short_description, description)

    def test_formfield_for_foreignkey(self):
        # foreign key forms fields in admin
        # for publishable models should be filtered
        # to hide public object

        request = None
        parent_field = None
        for field in Page._meta.fields:
            if field.name == 'parent':
                parent_field = field
                break
        self.failUnless(parent_field)

        choice_field = self.page_admin.formfield_for_foreignkey(parent_field,
                                                                request)
        self.failUnless(choice_field)
        self.failUnless(isinstance(choice_field, ModelChoiceField))

        self.failUnlessEqual(
            set([self.page1, self.page1.public, self.page2,
                 self.page2.public]),
            set(Page.objects.all())
        )
        self.failUnlessEqual(
            set([self.page1, self.page2]),
            set(choice_field.queryset)
        )

    def test_formfield_for_manytomany(self):
        request = None
        authors_field = None
        for field in Page._meta.many_to_many:
            if field.name == 'authors':
                authors_field = field
                break
        self.failUnless(authors_field)

        choice_field = self.page_admin.formfield_for_manytomany(authors_field,
                                                                request)
        self.failUnless(choice_field)
        self.failUnless(isinstance(choice_field, ModelMultipleChoiceField))

        self.failUnlessEqual(
            set([self.author1, self.author1.public, self.author2,
                 self.author2.public]),
            set(Author.objects.all())
        )
        self.failUnlessEqual(
            set([self.author1, self.author2]),
            set(choice_field.queryset)
        )

    def test_has_change_permission(self):
        class dummy_request(object):
            method = 'GET'
            REQUEST = {}

            class user(object):
                @classmethod
                def has_perm(cls, permission):
                    return True

        self.failUnless(self.page_admin.has_change_permission(dummy_request))
        self.failUnless(
            self.page_admin.has_change_permission(dummy_request, self.page1))
        self.failIf(self.page_admin.has_change_permission(dummy_request,
                                                          self.page1.public))

        # can view deleted items
        self.page1.publish_state = Publishable.PUBLISH_DELETE
        self.failUnless(
            self.page_admin.has_change_permission(dummy_request, self.page1))

        # but cannot modify them
        dummy_request.method = 'POST'
        self.failIf(
            self.page_admin.has_change_permission(dummy_request, self.page1))

    def test_has_delete_permission(self):
        class dummy_request(object):
            method = 'GET'
            REQUEST = {}

            class user(object):
                @classmethod
                def has_perm(cls, permission):
                    return True

        self.failUnless(self.page_admin.has_delete_permission(dummy_request))
        self.failUnless(
            self.page_admin.has_delete_permission(dummy_request, self.page1))
        self.failIf(self.page_admin.has_delete_permission(dummy_request,
                                                          self.page1.public))

    def test_change_view_normal(self):
        class dummy_request(object):
            method = 'GET'
            REQUEST = {}
            COOKIES = {}
            META = {}

            @classmethod
            def is_ajax(cls):
                return False

            @classmethod
            def is_secure(cls):
                return False

            class user(object):
                @classmethod
                def has_perm(cls, permission):
                    return True

                @classmethod
                def get_and_delete_messages(cls):
                    return []

        response = self.page_admin.change_view(dummy_request,
                                               str(self.page1.id))
        self.failUnless(response is not None)
        self.failIf('deleted' in _get_rendered_content(response))

    def test_change_view_not_deleted(self):
        class dummy_request(object):
            method = 'GET'
            COOKIES = {}
            META = {}

            @classmethod
            def is_ajax(cls):
                return False

            @classmethod
            def is_secure(cls):
                return False

            class user(object):
                @classmethod
                def has_perm(cls, permission):
                    return True

        try:
            self.page_admin.change_view(dummy_request,
                                        unicode(self.page1.public.id))
            self.fail()
        except Http404:
            pass

    def test_change_view_deleted(self):
        class dummy_request(object):
            method = 'GET'
            REQUEST = {}
            COOKIES = {}
            META = {}

            @classmethod
            def is_ajax(cls):
                return False

            @classmethod
            def is_secure(cls):
                return False

            class user(object):
                @classmethod
                def has_perm(cls, permission):
                    return True

                @classmethod
                def get_and_delete_messages(cls):
                    return []

        self.page1.delete()

        response = self.page_admin.change_view(dummy_request,
                                               str(self.page1.id))
        self.failUnless(response is not None)
        self.failUnless('deleted' in _get_rendered_content(response))

    def test_change_view_deleted_POST(self):
        class dummy_request(object):
            csrf_processing_done = True
            method = 'POST'
            COOKIES = {}
            META = {}
            POST = {}

            @classmethod
            def is_ajax(cls):
                return False

            @classmethod
            def is_secure(cls):
                return False

        self.page1.delete()

        try:
            self.page_admin.change_view(dummy_request, str(self.page1.id))
            self.fail()
        except PermissionDenied:
            pass

    def test_change_view_delete_inline(self):
        block = PageBlock.objects.create(page=self.page1,
                                         content='some content')
        page1 = Page.objects.get(pk=self.page1.pk)
        page1.publish()

        user1 = User.objects.create_user('test1', 'test@example.com', 'jkljkl')

        # fake selecting the delete tickbox for the block

        class dummy_request(object):
            csrf_processing_done = True
            method = 'POST'

            POST = {
                'slug': page1.slug,
                'title': page1.title,
                'content': page1.content,
                'pub_date_0': '2010-02-12',
                'pub_date_1': '17:40:00',
                'pageblock_set-TOTAL_FORMS': '2',
                'pageblock_set-INITIAL_FORMS': '1',
                'pageblock_set-0-id': str(block.id),
                'pageblock_set-0-page': str(page1.id),
                'pageblock_set-0-DELETE': 'yes'
            }
            REQUEST = POST
            FILES = {}
            COOKIES = {}
            META = {}

            @classmethod
            def is_ajax(cls):
                return False

            @classmethod
            def is_secure(cls):
                return False

            class user(object):
                pk = user1.pk

                @classmethod
                def is_authenticated(self):
                    return True

                @classmethod
                def has_perm(cls, permission):
                    return True

                @classmethod
                def get_and_delete_messages(cls):
                    return []

                class message_set(object):
                    @classmethod
                    def create(cls, message=''):
                        pass

            class _messages(object):
                @classmethod
                def add(cls, *message):
                    pass

        block = PageBlock.objects.get(id=block.id)
        public_block = block.public

        response = self.page_admin.change_view(dummy_request, str(page1.id))
        self.assertEqual(302, response.status_code)

        # the block should have been deleted (but not the public one)
        self.failUnlessEqual([public_block], list(PageBlock.objects.all()))


class PublishPage(TestCase):
    def setUp(self):
        super(PublishPage, self).setUp()
        self.admin_site = AdminSite('Test Admin')

        class PageAdmin(PublishableAdmin):
            pass

        self.admin_site.register(Page, PageAdmin)
        self.page_admin = PageAdmin(Page, self.admin_site)

    def test_should_be_publish(self):
        self.page1 = Page.objects.create(slug='page1', title='page 1')

        user1 = User.objects.create_superuser('test1', 'test@example.com',
                                              'pass')

        self.factory = RequestFactory()
        request = self.factory.post('/publish/change_view',
                                    data={'_publish': ''})
        request.user = user1

        self.page_admin.change_view(request, str(self.page1.id))
        self.assertEqual(Page.objects.filter(Page.Q_PUBLISHED,
                                             slug=self.page1.slug).count(), 1)

    def test_should_be_republish(self):
        self.page1 = Page.objects.create(slug='page1', title='page 1')
        self.page1.publish()
        user1 = User.objects.create_superuser('test1', 'test@example.com',
                                              'pass')

        self.factory = RequestFactory()
        request = self.factory.post('/publish/change_view',
                                    data={'_publish': ''})
        request.user = user1

        self.page_admin.change_view(request, str(self.page1.id))
        self.assertEqual(Page.objects.filter(Page.Q_PUBLISHED,
                                             slug=self.page1.slug).count(), 1)
