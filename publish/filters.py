from django.utils.encoding import smart_unicode
from .models import Publishable
from django.contrib.admin.filters import FieldListFilter, \
    RelatedFieldListFilter


def is_publishable_filter(f):
    return bool(f.rel) and issubclass(f.rel.to, Publishable)


class PublishableRelatedFieldListFilter(RelatedFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, *arg, **kw):
        super(PublishableRelatedFieldListFilter, self).__init__(field, request,
                                                                params, model,
                                                                model_admin,
                                                                *arg, **kw)
        # to keep things simple we'll just remove all "non-draft"
        # instance from list
        rel_model = field.rel.to
        queryset = rel_model._default_manager.complex_filter(
            field.rel.limit_choices_to).draft_and_deleted()
        if hasattr(field.rel, 'get_related_field'):
            lst = [(getattr(x, field.rel.get_related_field().attname),
                    smart_unicode(x)) for x in queryset]
        else:
            lst = [(x._get_pk_val(), smart_unicode(x)) for x in queryset]
        self.lookup_choices = lst


def register_filters():
    FieldListFilter.register(is_publishable_filter,
                             PublishableRelatedFieldListFilter,
                             take_priority=True)
