from django.test import TestCase
from publish.models import Publishable
from publish.tests.example_app.models import Page, PageBlock, Comment

__author__ = 'petry'


class TestPublishableRecursiveForeignKey(TestCase):

    def setUp(self):
        super(TestPublishableRecursiveForeignKey, self).setUp()
        self.page1 = Page.objects.create(slug='page1', title='page 1', content='some content')
        self.page2 = Page.objects.create(slug='page2', title='page 2', content='other content', parent=self.page1)

    def test_publish_parent(self):
        # this shouldn't publish the child page
        self.page1.publish()
        self.failUnless(self.page1.public)
        self.failIf(self.page1.public.parent)

        page2 = Page.objects.get(id=self.page2.id)
        self.failIf(page2.public)

    def test_publish_child_parent_already_published(self):
        self.page1.publish()
        self.page2.publish()

        self.failUnless(self.page1.public)
        self.failUnless(self.page2.public)

        self.failIf(self.page1.public.parent)
        self.failUnless(self.page2.public.parent)

        self.failIfEqual(self.page1, self.page2.public.parent)

        self.failUnlessEqual('/page1/', self.page1.public.get_absolute_url())
        self.failUnlessEqual('/page1/page2/', self.page2.public.get_absolute_url())

    def test_publish_child_parent_not_already_published(self):
        self.page2.publish()

        page1 = Page.objects.get(id=self.page1.id)
        self.failUnless(page1.public)
        self.failUnless(self.page2.public)

        self.failIf(page1.public.parent)
        self.failUnless(self.page2.public.parent)

        self.failIfEqual(page1, self.page2.public.parent)

        self.failUnlessEqual('/page1/', self.page1.public.get_absolute_url())
        self.failUnlessEqual('/page1/page2/', self.page2.public.get_absolute_url())

    def test_publish_repeated(self):
        self.page1.publish()
        self.page2.publish()

        self.page1.slug='main'
        self.page1.save()

        self.failUnlessEqual('/main/', self.page1.get_absolute_url())

        page1 = Page.objects.get(id=self.page1.id)
        page2 = Page.objects.get(id=self.page2.id)
        self.failUnlessEqual('/page1/', page1.public.get_absolute_url())
        self.failUnlessEqual('/page1/page2/', page2.public.get_absolute_url())

        page1.publish()
        page1 = Page.objects.get(id=self.page1.id)
        page2 = Page.objects.get(id=self.page2.id)
        self.failUnlessEqual('/main/', page1.public.get_absolute_url())
        self.failUnlessEqual('/main/page2/', page2.public.get_absolute_url())

        page1.slug='elsewhere'
        page1.save()
        page1 = Page.objects.get(id=self.page1.id)
        page2 = Page.objects.get(id=self.page2.id)
        page2.slug='meanwhile'
        page2.save()
        page2.publish()
        page1 = Page.objects.get(id=self.page1.id)
        page2 = Page.objects.get(id=self.page2.id)

        # only page2 should be published, not page1, as page1 already published
        self.failUnlessEqual(Publishable.PUBLISH_DEFAULT, page2.publish_state)
        self.failUnlessEqual(Publishable.PUBLISH_CHANGED, page1.publish_state)

        self.failUnlessEqual('/main/', page1.public.get_absolute_url())
        self.failUnlessEqual('/main/meanwhile/', page2.public.get_absolute_url())

        page1.publish()
        page1 = Page.objects.get(id=self.page1.id)
        page2 = Page.objects.get(id=self.page2.id)

        self.failUnlessEqual(Publishable.PUBLISH_DEFAULT, page2.publish_state)
        self.failUnlessEqual(Publishable.PUBLISH_DEFAULT, page1.publish_state)

        self.failUnlessEqual('/elsewhere/', page1.public.get_absolute_url())
        self.failUnlessEqual('/elsewhere/meanwhile/', page2.public.get_absolute_url())

    def test_publish_deletions(self):
        self.page1.publish()
        self.page2.publish()

        self.page2.delete()
        self.failUnlessEqual([self.page2], list(Page.objects.deleted()))

        self.page2.publish()
        self.failUnlessEqual([self.page1.public], list(Page.objects.published()))
        self.failUnlessEqual([], list(Page.objects.deleted()))

    def test_publish_reverse_fields(self):
        page_block = PageBlock.objects.create(page=self.page1, content='here we are')

        self.page1.publish()

        public = self.page1.public
        self.failUnless(public)

        blocks = list(public.pageblock_set.all())
        self.failUnlessEqual(1, len(blocks))
        self.failUnlessEqual(page_block.content, blocks[0].content)

    def test_publish_deletions_reverse_fields(self):
        page_block = PageBlock.objects.create(page=self.page1, content='here we are')

        self.page1.publish()
        public = self.page1.public
        self.failUnless(public)

        self.page1.delete()

        self.failUnlessEqual([self.page1], list(Page.objects.deleted()))

        self.page1.publish()
        self.failUnlessEqual([], list(Page.objects.deleted()))
        self.failUnlessEqual([], list(Page.objects.all()))

    def test_publish_reverse_fields_deleted(self):
        # make sure child elements get removed
        page_block = PageBlock.objects.create(page=self.page1, content='here we are')

        self.page1.publish()

        public = self.page1.public
        page_block = PageBlock.objects.get(id=page_block.id)
        page_block_public = page_block.public
        self.failIf(page_block_public is None)

        self.failUnlessEqual([page_block_public], list(public.pageblock_set.all()))

        # now delete the page block and publish the parent
        # to make sure that deletion gets copied over properly
        page_block.delete()
        page1 = Page.objects.get(id=self.page1.id)
        page1.publish()
        public = page1.public

        self.failUnlessEqual([], list(public.pageblock_set.all()))

    def test_publish_delections_with_non_publishable_children(self):
        self.page1.publish()

        comment = Comment.objects.create(page=self.page1.public, comment='This is a comment')

        self.failUnlessEqual(1, Comment.objects.count())

        self.page1.delete()

        self.failUnlessEqual([self.page1], list(Page.objects.deleted()))
        self.failIf(self.page1 in Page.objects.draft())

        self.page1.publish()
        self.failUnlessEqual([], list(Page.objects.deleted()))
        self.failUnlessEqual([], list(Page.objects.all()))
        self.failUnlessEqual([], list(Comment.objects.all()))