from .models import User, Group, Location
from rest_framework.serializers import CharField

from dynamic_rest.fields import (
    CountField,
    DynamicField,
    DynamicGenericRelationField,
    DynamicMethodField,
    DynamicRelationField,
    ValidationError)
from dynamic_rest.serializers import (
    DynamicEphemeralSerializer,
    DynamicModelSerializer
)


class DynamicRelationFieldUpdated(DynamicRelationField):

    def __init__(self,
            serializer_class,
            many=False,
            queryset=None,
            embed=False,
            sideloading=None,
            debug=False,
            **kwargs):

        self._serializer_class = serializer_class
        self.bound = False
        self.queryset = queryset
        self.sideloading = sideloading
        self.debug = debug
        self.embed = embed if sideloading is None else not sideloading
        if '.' in kwargs.get('source', ''):
            raise Exception('Nested relationships are not supported')
        if 'link' in kwargs:
            self.link = kwargs.pop('link')
        super(DynamicRelationField, self).__init__(**kwargs)
        self.kwargs['many'] = self.many = many

    def to_representation(self, instance):
        """Represent the relationship, either as an ID or object."""
        serializer = self.serializer
        model = serializer.get_model()
        source = self.source

        if not self.kwargs['many'] and serializer.id_only():
            # attempt to optimize by reading the related ID directly
            # from the current instance rather than from the related object
            source_id = '%s_id' % source
            # try the faster way first:
            if hasattr(instance, source_id):
                return getattr(instance, "uid")
            elif model is not None:
                # this is probably a one-to-one field, or a reverse related
                # lookup, so let's look it up the slow way and let the
                # serializer handle the id dereferencing
                try:
                    instance = getattr(instance, source)
                except model.DoesNotExist:
                    instance = None

        # dereference ephemeral objects
        if model is None:
            instance = getattr(instance, source)

        if instance is None:
            return None

        return serializer.to_representation(instance)

    def to_internal_value_single(self, data, serializer):
        """Return the underlying object, given the serialized form."""
        related_model = serializer.Meta.model
        if isinstance(data, related_model):
            return data
        try:
            instance = related_model.objects.get(uid=data)
        except related_model.DoesNotExist:
            raise ValidationError(
                "Invalid value for '%s': %s object with ID=%s not found" %
                (self.field_name, related_model.__name__, data)
            )
        return instance


class UserSerializer(DynamicModelSerializer):

    class Meta:
        model = User
        name = 'user'
        fields = (
            'uid',
            'name',
            'groups',
            'location',
            'data'
        )
        deferred_fields = ('id')

    location = DynamicRelationFieldUpdated('LocationSerializer')
    groups = DynamicRelationFieldUpdated('GroupSerializer', many=True, deferred=True)


class GroupSerializer(DynamicModelSerializer):

    class Meta:
        model = Group
        name = 'group'
        fields = (
            'uid',
            'name',
            'location',
            'data'
        )
        deferred_fields = ('id')

    location = DynamicRelationFieldUpdated('LocationSerializer')



class LocationSerializer(DynamicModelSerializer):

    class Meta:
        model = Location
        name = 'location'
        fields = (
            'uid',
            'name',
            'data'
        )
        deferred_fields = ('id')





