from rest_framework.filters import BaseFilterBackend
from django.core.exceptions import ValidationError as InternalValidationError
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q, Prefetch, Manager
from django.utils import six
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, NullBooleanField
from rest_framework.filters import BaseFilterBackend, OrderingFilter
from django.contrib.postgres.fields import JSONField


from dynamic_rest.utils import is_truthy
from dynamic_rest.conf import settings
from dynamic_rest.datastructures import TreeMap
from dynamic_rest.fields import DynamicRelationField
from dynamic_rest.meta import (
    get_model_field,
    is_field_remote,
    is_model_field,
    get_related_model
)
from dynamic_rest.patches import patch_prefetch_one_level
from dynamic_rest.prefetch import FastQuery, FastPrefetch
from dynamic_rest.related import RelatedObject

patch_prefetch_one_level()
from dynamic_rest.filters import FilterNode, DynamicFilterBackend


class FilterNodeUpdated(FilterNode):


    def generate_query_key(self, serializer):
        """Get the key that can be passed to Django's filter method.

        To account for serialier field name rewrites, this method
        translates serializer field names to model field names
        by inspecting `serializer`.

        For example, a query like `filter{users.events}` would be
        returned as `users__events`.

        Arguments:
            serializer: A DRF serializer

        Returns:
            A filter key.
        """
        rewritten = []
        last = len(self.field) - 1
        s = serializer
        field = None

        for i, field_name in enumerate(self.field):
            # Note: .fields can be empty for related serializers that aren't
            # sideloaded. Fields that are deferred also won't be present.
            # If field name isn't in serializer.fields, get full list from
            # get_all_fields() method. This is somewhat expensive, so only do
            # this if we have to.
            fields = s.fields
            field_name_split = field_name.split('_')
            field_name_first = field_name_split[0]

            if field_name_first not in fields:
                fields = getattr(s, 'get_all_fields', lambda: {})()

            if field_name == 'pk':
                rewritten.append('pk')
                continue

            if field_name_first not in fields:
                raise ValidationError(
                    "Invalid filter field: %s" % field_name
                )

            field = fields[field_name_first]

            # For remote fields, strip off '_set' for filtering. This is a
            # weird Django inconsistency.
            model_field_name = field.source or field_name
            model_field = get_model_field(s.get_model(), model_field_name)
            if isinstance(model_field, RelatedObject):
                model_field_name = model_field.field.related_query_name()

            # If get_all_fields() was used above, field could be unbound,
            # and field.source would be None
            rewritten.append(model_field_name)

            if i == last:
                break

            # Recurse into nested field
            s = getattr(field, 'serializer', None)
            if isinstance(s, serializers.ListSerializer):
                s = s.child
            if not s:
                raise ValidationError(
                    "Invalid nested filter field: %s" % field_name
                )

        if self.operator:
            rewritten.append(self.operator)

        return ('__'.join(rewritten), field)


class DynamicFilterBackendUpdated(DynamicFilterBackend):

    """A DRF filter backend that constructs DREST querysets.

    This backend is responsible for interpretting and applying
    filters, includes, and excludes to the base queryset of a view.

    Attributes:
        VALID_FILTER_OPERATORS: A list of filter operators.
    """

    VALID_FILTER_OPERATORS = (
        'in',
        'any',
        'all',
        'icontains',
        'contains',
        'startswith',
        'istartswith',
        'endswith',
        'iendswith',
        'year',
        'month',
        'day',
        'week_day',
        'regex',
        'range',
        'gt',
        'lt',
        'gte',
        'lte',
        'isnull',
        'eq',
        'iexact',
        'overlap',
        None,
    )

    def filter_queryset(self, request, queryset, view):
        """Filter the queryset.

        This is the main entry-point to this class, and
        is called by DRF's list handler.
        """
        self.request = request
        self.view = view

        # enable addition of extra filters (i.e., a Q())
        # so custom filters can be added to the queryset without
        # running into https://code.djangoproject.com/ticket/18437
        # which, without this, would mean that filters added to the queryset
        # after this is called may not behave as expected
        extra_filters = self.view.get_extra_filters(request)

        disable_prefetches = self.view.is_update()

        self.DEBUG = settings.DEBUG

        return self._build_queryset(
            queryset=queryset,
            extra_filters=extra_filters,
            disable_prefetches=disable_prefetches,
        )

    """
    This function was renamed and broke downstream dependencies that haven't
    been updated to use the new naming convention.
    """
    def _extract_filters(self, **kwargs):
        return self._get_requested_filters(**kwargs)

    def _get_requested_filters(self, **kwargs):
        """
        Convert 'filters' query params into a dict that can be passed
        to Q. Returns a dict with two fields, 'include' and 'exclude',
        which can be used like:

          result = self._get_requested_filters()
          q = Q(**result['include'] & ~Q(**result['exclude'])

        """

        filters_map = (
            kwargs.get('filters_map') or
            self.view.get_request_feature(self.view.FILTER)
        )

        out = TreeMap()

        for spec, value in six.iteritems(filters_map):

            # Inclusion or exclusion?
            if spec[0] == '-':
                spec = spec[1:]
                inex = '_exclude'
            else:
                inex = '_include'

            # for relational filters, separate out relation path part
            if '|' in spec:
                rel, spec = spec.split('|')
                rel = rel.split('.')
            else:
                rel = None

            parts = spec.split('.')

            # Last part could be operator, e.g. "events.capacity.gte"
            if len(parts) > 1 and parts[-1] in self.VALID_FILTER_OPERATORS:
                operator = parts.pop()
            else:
                operator = None

            # All operators except 'range' and 'in' should have one value
            if operator == 'range':
                value = value[:2]
            elif operator == 'in':
                # no-op: i.e. accept `value` as an arbitrarily long list
                pass
            elif operator in self.VALID_FILTER_OPERATORS:
                value = value[0]
                if (
                    operator == 'isnull' and
                    isinstance(value, six.string_types)
                ):
                    value = is_truthy(value)
                elif operator == 'eq':
                    operator = None

            node = FilterNodeUpdated(parts, operator, value)

            # insert into output tree
            path = rel if rel else []
            path += [inex, node.key]
            out.insert(path, node)

        return out
