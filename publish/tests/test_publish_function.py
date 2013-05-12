from django.test import TestCase
from publish.tests.example_app.models import Page, update_pub_date

__author__ = 'petry'


class TestPublishFunction(TestCase):

    def setUp(self):
        super(TestPublishFunction, self).setUp()
        self.page = Page.objects.create(slug='page', title='Page')

    def test_publish_function_invoked(self):
        # check we can override default copy behaviour

        from datetime import datetime

        pub_date = datetime(2000, 1, 1)
        update_pub_date.pub_date = pub_date

        self.failIfEqual(pub_date, self.page.pub_date)

        self.page.publish()
        self.failIfEqual(pub_date, self.page.pub_date)
        self.failUnlessEqual(pub_date, self.page.public.pub_date)