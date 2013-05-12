from django.conf import settings
from django.conf.urls import patterns, include
from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from publish.actions import delete_selected
from publish.admin import PublishableAdmin
from publish.tests.example_app.models import FlatPage


class TestDeleteSelected(TestCase):
    def setUp(self):
        super(TestDeleteSelected, self).setUp()
        self.fp1 = FlatPage.objects.create(url='/fp1', title='FP1')
        self.fp2 = FlatPage.objects.create(url='/fp2', title='FP2')
        self.fp3 = FlatPage.objects.create(url='/fp3', title='FP3')

        self.fp1.publish()
        self.fp2.publish()
        self.fp3.publish()

        self.admin_site = AdminSite('Test Admin')
        self.page_admin = PublishableAdmin(FlatPage, self.admin_site)

        # override urls, so reverse works
        settings.ROOT_URLCONF = patterns(
            '',
            ('^admin/',
             include(self.admin_site.urls)),
        )

    def test_delete_selected_check_cannot_delete_public(self):
        # delete won't work (via admin) for public instances
        request = None
        self.assertRaises(PermissionDenied, delete_selected, self.page_admin,
                          request, FlatPage.objects.published())

    def test_delete_selected(self):
        class dummy_request(object):
            POST = {}
            META = {}

            class user(object):
                @classmethod
                def has_perm(cls, *arg):
                    return True

                @classmethod
                def get_and_delete_messages(cls):
                    return []

        response = delete_selected(self.page_admin, dummy_request,
                                   FlatPage.objects.draft())
        self.failUnless(response is not None)
