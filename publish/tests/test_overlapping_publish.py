from django.test import TestCase
from publish.tests.example_app.models import Page
from publish.utils import NestedSet

__author__ = 'petry'


class TestOverlappingPublish(TestCase):

    def setUp(self):
        self.page1 = Page.objects.create(slug='page1', title='page 1')
        self.page2 = Page.objects.create(slug='page2', title='page 2')
        self.child1 = Page.objects.create(parent=self.page1, slug='child1', title='Child 1')
        self.child2 = Page.objects.create(parent=self.page1, slug='child2', title='Child 2')
        self.child3 = Page.objects.create(parent=self.page2, slug='child3', title='Child 3')

    def test_publish_with_overlapping_models(self):
        # make sure when we publish we don't accidentally create
        # multiple published versions
        self.failUnlessEqual(5, Page.objects.draft().count())
        self.failUnlessEqual(0, Page.objects.published().count())

        Page.objects.draft().publish()

        self.failUnlessEqual(5, Page.objects.draft().count())
        self.failUnlessEqual(5, Page.objects.published().count())

    def test_publish_with_overlapping_models_published(self):
        # make sure when we publish we don't accidentally create
        # multiple published versions
        self.failUnlessEqual(5, Page.objects.draft().count())
        self.failUnlessEqual(0, Page.objects.published().count())

        all_published = NestedSet()
        Page.objects.draft().publish(all_published)

        self.failUnlessEqual(5, len(all_published))

        self.failUnlessEqual(5, Page.objects.draft().count())
        self.failUnlessEqual(5, Page.objects.published().count())

    def test_publish_after_dry_run_handles_caching(self):
        # if we do a dry tun publish in the same queryset
        # before publishing for real, we have to make
        # sure we don't run into issues with the instance
        # caching parent's as None
        self.failUnlessEqual(5, Page.objects.draft().count())
        self.failUnlessEqual(0, Page.objects.published().count())

        draft = Page.objects.draft()

        all_published = NestedSet()
        for p in draft:
            p.publish(dry_run=True, all_published=all_published)

        # nothing published yet
        self.failUnlessEqual(5, Page.objects.draft().count())
        self.failUnlessEqual(0, Page.objects.published().count())

        # now publish (using same queryset, as this will have cached the instances)
        draft.publish()

        self.failUnlessEqual(5, Page.objects.draft().count())
        self.failUnlessEqual(5, Page.objects.published().count())

        # now actually check the public parent's are setup right
        page1 = Page.objects.get(id=self.page1.id)
        page2 = Page.objects.get(id=self.page2.id)
        child1 = Page.objects.get(id=self.child1.id)
        child2 = Page.objects.get(id=self.child2.id)
        child3 = Page.objects.get(id=self.child3.id)

        self.failUnlessEqual(None, page1.public.parent)
        self.failUnlessEqual(None, page2.public.parent)
        self.failUnlessEqual(page1.public, child1.public.parent)
        self.failUnlessEqual(page1.public, child2.public.parent)
        self.failUnlessEqual(page2.public, child3.public.parent)