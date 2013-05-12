from django.test import TestCase
from publish.tests.example_app.models import Page


class TestInfiniteRecursion(TestCase):
    def setUp(self):
        super(TestInfiniteRecursion, self).setUp()

        self.page1 = Page.objects.create(slug='page1', title='page 1')
        self.page2 = Page.objects.create(slug='page2', title='page 2',
                                         parent=self.page1)
        self.page1.parent = self.page2
        self.page1.save()

    def test_publish_recursion_breaks(self):
        self.page1.publish()  # this should simple run without an error
