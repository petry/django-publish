from django.test import TestCase
from publish.tests.example_app.models import Page, Tag, PageTagOrder

__author__ = 'petry'


class TestManyToManyThrough(TestCase):

    def setUp(self):
        super(TestManyToManyThrough, self).setUp()
        self.page = Page.objects.create(slug='p1', title='P 1')
        self.tag1 = Tag.objects.create(slug='tag1', title='Tag 1')
        self.tag2 = Tag.objects.create(slug='tag2', title='Tag 2')
        PageTagOrder.objects.create(tagged_page=self.page, page_tag=self.tag1, tag_order=2)
        PageTagOrder.objects.create(tagged_page=self.page, page_tag=self.tag2, tag_order=1)

    def test_publish_copies_tags(self):
        self.page.publish()

        self.failUnlessEqual(set([self.tag1, self.tag2]), set(self.page.public.tags.all()))