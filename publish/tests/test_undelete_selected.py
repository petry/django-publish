from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from publish.actions import undelete_selected
from publish.admin import PublishableAdmin
from publish.models import Publishable
from publish.tests.example_app.models import FlatPage

__author__ = 'petry'


class TestUndeleteSelected(TestCase):

    def setUp(self):
        super(TestUndeleteSelected, self).setUp()
        self.fp1 = FlatPage.objects.create(url='/fp1', title='FP1')

        self.fp1.publish()

        self.admin_site = AdminSite('Test Admin')
        self.page_admin = PublishableAdmin(FlatPage, self.admin_site)

    def test_undelete_selected(self):
        class dummy_request(object):

            class user(object):
                @classmethod
                def has_perm(cls, *arg):
                    return True

        self.fp1.delete()
        self.failUnlessEqual(Publishable.PUBLISH_DELETE, self.fp1.publish_state)

        response = undelete_selected(self.page_admin, dummy_request, FlatPage.objects.deleted())
        self.failUnless(response is None)

        # publish state should no longer be delete
        fp1 = FlatPage.objects.get(pk=self.fp1.pk)
        self.failUnlessEqual(Publishable.PUBLISH_CHANGED, fp1.publish_state)

    def test_undelete_selected_no_permission(self):
        class dummy_request(object):

            class user(object):
                @classmethod
                def has_perm(cls, *arg):
                    return False

        self.fp1.delete()
        self.failUnlessEqual(Publishable.PUBLISH_DELETE, self.fp1.publish_state)

        self.assertRaises(PermissionDenied, undelete_selected, self.page_admin, dummy_request, FlatPage.objects.deleted())