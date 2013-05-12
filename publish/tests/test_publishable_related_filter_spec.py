from django.test import TestCase
from publish.admin import PublishableAdmin
from publish.filters import FieldListFilter, PublishableRelatedFieldListFilter
from publish.tests.example_app.models import Page, Author




class TestPublishableRelatedFilterSpec(TestCase):

    def test_overridden_spec(self):
        # make sure the publishable filter spec
        # gets used when we use a publishable field
        class dummy_request(object):
            GET = {}

        spec = FieldListFilter.create(Page._meta.get_field('authors'), dummy_request, {}, Page, PublishableAdmin, None)
        self.failUnless(isinstance(spec, PublishableRelatedFieldListFilter))

    def test_only_draft_shown(self):
        self.author = Author.objects.create(name='author')
        self.author.publish()

        self.failUnless(2, Author.objects.count())

        # make sure the publishable filter spec
        # gets used when we use a publishable field
        class dummy_request(object):
            GET = {}

        spec = FieldListFilter.create(Page._meta.get_field('authors'), dummy_request, {}, Page, PublishableAdmin, None)

        lookup_choices = spec.lookup_choices
        self.failUnlessEqual(1, len(lookup_choices))
        pk, label = lookup_choices[0]
        self.failUnlessEqual(self.author.id, pk)