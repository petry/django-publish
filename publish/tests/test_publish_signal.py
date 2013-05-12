from django.test import TestCase
from publish.models import Publishable
from publish.signals import pre_publish, post_publish
from publish.tests.example_app.models import Page




class TestPublishSignals(TestCase):

    def setUp(self):
        self.page1  = Page.objects.create(slug='page1', title='page 1')
        self.page2  = Page.objects.create(slug='page2', title='page 2')
        self.child1 = Page.objects.create(parent=self.page1, slug='child1', title='Child 1')
        self.child2 = Page.objects.create(parent=self.page1, slug='child2', title='Child 2')
        self.child3 = Page.objects.create(parent=self.page2, slug='child3', title='Child 3')

        self.failUnlessEqual(5, Page.objects.draft().count())

    def _check_pre_publish(self, queryset):
        pre_published = []
        def pre_publish_handler(sender, instance, **kw):
            pre_published.append(instance)

        pre_publish.connect(pre_publish_handler, sender=Page)

        queryset.draft().publish()

        self.failUnlessEqual(queryset.draft().count(), len(pre_published))
        self.failUnlessEqual(set(queryset.draft()), set(pre_published))

    def test_pre_publish(self):
        # page order shouldn't matter when publishing
        # should always get the right number of signals
        self._check_pre_publish(Page.objects.order_by('id'))
        self._check_pre_publish(Page.objects.order_by('-id'))
        self._check_pre_publish(Page.objects.order_by('?'))

    def _check_post_publish(self, queryset):
        published = []
        def post_publish_handler(sender, instance, **kw):
            published.append(instance)

        post_publish.connect(post_publish_handler, sender=Page)

        queryset.draft().publish()

        self.failUnlessEqual(queryset.draft().count(), len(published))
        self.failUnlessEqual(set(queryset.draft()), set(published))

    def test_post_publish(self):
        self._check_post_publish(Page.objects.order_by('id'))
        self._check_post_publish(Page.objects.order_by('-id'))
        self._check_post_publish(Page.objects.order_by('?'))

    def test_signals_sent_for_followed(self):
        pre_published = []
        def pre_publish_handler(sender, instance, **kw):
            pre_published.append(instance)

        pre_publish.connect(pre_publish_handler, sender=Page)

        published = []
        def post_publish_handler(sender, instance, **kw):
            published.append(instance)

        post_publish.connect(post_publish_handler, sender=Page)

        # publishing just children will also publish it's parent (if needed)
        # which should also fire signals

        self.child1.publish()

        self.failUnlessEqual(set([self.page1, self.child1]), set(pre_published))
        self.failUnlessEqual(set([self.page1, self.child1]), set(published))

    def test_deleted_flag_false_when_publishing_change(self):
        def pre_publish_handler(sender, instance, deleted, **kw):
            self.failIf(deleted)

        pre_publish.connect(pre_publish_handler, sender=Page)

        def post_publish_handler(sender, instance, deleted, **kw):
            self.failIf(deleted)

        post_publish.connect(post_publish_handler, sender=Page)

        self.page1.publish()

    def test_deleted_flag_true_when_publishing_deletion(self):
        self.child1.publish()
        public = self.child1.public

        self.child1.delete()

        self.failUnlessEqual(Publishable.PUBLISH_DELETE, self.child1.publish_state)

        def pre_publish_handler(sender, instance, deleted, **kw):
            self.failUnless(deleted)

        pre_publish.connect(pre_publish_handler, sender=Page)

        def post_publish_handler(sender, instance, deleted, **kw):
            self.failUnless(deleted)

        post_publish.connect(post_publish_handler, sender=Page)

        self.child1.publish()