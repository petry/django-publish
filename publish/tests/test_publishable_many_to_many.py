from django.test import TestCase
from publish.tests.example_app.models import FlatPage, Site


class TestPublishableManyToMany(TestCase):
    def setUp(self):
        super(TestPublishableManyToMany, self).setUp()
        self.flat_page = FlatPage.objects.create(
            url='/my-page', title='my page',
            content='here is some content',
            enable_comments=False,
            registration_required=True)
        self.site1 = Site.objects.create(title='my site', domain='mysite.com')
        self.site2 = Site.objects.create(title='a site', domain='asite.com')

    def test_publish_no_sites(self):
        self.flat_page.publish()
        self.failUnless(self.flat_page.public)
        self.failUnlessEqual([], list(self.flat_page.public.sites.all()))

    def test_publish_add_site(self):
        self.flat_page.sites.add(self.site1)
        self.flat_page.publish()
        self.failUnless(self.flat_page.public)
        self.failUnlessEqual([self.site1],
                             list(self.flat_page.public.sites.all()))

    def test_publish_repeated_add_site(self):
        self.flat_page.sites.add(self.site1)
        self.flat_page.publish()
        self.failUnless(self.flat_page.public)
        self.failUnlessEqual([self.site1],
                             list(self.flat_page.public.sites.all()))

        self.flat_page.sites.add(self.site2)
        self.failUnlessEqual([self.site1],
                             list(self.flat_page.public.sites.all()))

        self.flat_page.publish()
        self.failUnlessEqual([self.site1, self.site2],
                             list(self.flat_page.public.sites.order_by('id')))

    def test_publish_remove_site(self):
        self.flat_page.sites.add(self.site1, self.site2)
        self.flat_page.publish()
        self.failUnless(self.flat_page.public)
        self.failUnlessEqual([self.site1, self.site2],
                             list(self.flat_page.public.sites.order_by('id')))

        self.flat_page.sites.remove(self.site1)
        self.failUnlessEqual([self.site1, self.site2],
                             list(self.flat_page.public.sites.order_by('id')))

        self.flat_page.publish()
        self.failUnlessEqual([self.site2],
                             list(self.flat_page.public.sites.all()))

    def test_publish_clear_sites(self):
        self.flat_page.sites.add(self.site1, self.site2)
        self.flat_page.publish()
        self.failUnless(self.flat_page.public)
        self.failUnlessEqual([self.site1, self.site2],
                             list(self.flat_page.public.sites.order_by('id')))

        self.flat_page.sites.clear()
        self.failUnlessEqual([self.site1, self.site2],
                             list(self.flat_page.public.sites.order_by('id')))

        self.flat_page.publish()
        self.failUnlessEqual([], list(self.flat_page.public.sites.all()))

    def test_publish_sites_cleared_not_deleted(self):
        self.flat_page.sites.add(self.site1, self.site2)
        self.flat_page.publish()
        self.flat_page.sites.clear()
        self.flat_page.publish()

        self.failUnlessEqual([], list(self.flat_page.public.sites.all()))

        self.failIfEqual([], list(Site.objects.all()))
