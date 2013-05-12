from django.test import TestCase
from publish.tests.example_app.models import Page, Author

__author__ = 'petry'


class TestPublishableRecursiveManyToManyField(TestCase):

    def setUp(self):
        super(TestPublishableRecursiveManyToManyField, self).setUp()
        self.page = Page.objects.create(slug='page1', title='page 1', content='some content')
        self.author1 = Author.objects.create(name='author1', profile='a profile')
        self.author2 = Author.objects.create(name='author2', profile='something else')

    def test_publish_add_author(self):
        self.page.authors.add(self.author1)
        self.page.publish()
        self.failUnless(self.page.public)

        author1 = Author.objects.get(id=self.author1.id)
        self.failUnless(author1.public)
        self.failIfEqual(author1.id, author1.public.id)
        self.failUnlessEqual(author1.name, author1.public.name)
        self.failUnlessEqual(author1.profile, author1.public.profile)

        self.failUnlessEqual([author1.public], list(self.page.public.authors.all()))

    def test_publish_repeated_add_author(self):
        self.page.authors.add(self.author1)
        self.page.publish()

        self.failUnless(self.page.public)

        self.page.authors.add(self.author2)
        author1 = Author.objects.get(id=self.author1.id)
        self.failUnlessEqual([author1.public], list(self.page.public.authors.all()))

        self.page.publish()
        author1 = Author.objects.get(id=self.author1.id)
        author2 = Author.objects.get(id=self.author2.id)
        self.failUnlessEqual([author1.public, author2.public], list(self.page.public.authors.order_by('name')))

    def test_publish_clear_authors(self):
        self.page.authors.add(self.author1, self.author2)
        self.page.publish()

        author1 = Author.objects.get(id=self.author1.id)
        author2 = Author.objects.get(id=self.author2.id)
        self.failUnlessEqual([author1.public, author2.public], list(self.page.public.authors.order_by('name')))

        self.page.authors.clear()
        self.failUnlessEqual([author1.public, author2.public], list(self.page.public.authors.order_by('name')))

        self.page.publish()
        self.failUnlessEqual([], list(self.page.public.authors.all()))