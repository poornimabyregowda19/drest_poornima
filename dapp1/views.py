from dynamic_rest.filters import DynamicSortingFilter
from rest_framework import exceptions
from django.db.models import Q

from dynamic_rest.viewsets import DynamicModelViewSet

from .filters import DynamicFilterBackendUpdated
from .serializers import UserSerializer, GroupSerializer, LocationSerializer
from .models import User,Group,Location

class UserViewSet(DynamicModelViewSet):
    features = (
        DynamicModelViewSet.INCLUDE, DynamicModelViewSet.EXCLUDE,
        DynamicModelViewSet.FILTER, DynamicModelViewSet.SORT,
        DynamicModelViewSet.SIDELOADING, DynamicModelViewSet.DEBUG
    )
    model = User
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = 'uid'
    filter_backends = (DynamicFilterBackendUpdated, DynamicSortingFilter)

    def get_queryset(self):
        location = self.request.query_params.get('location')
        qs = self.queryset
        if location:
            qs = qs.filter(location=location)
        return qs

    def list(self, request, *args, **kwargs):
        query_params = self.request.query_params
        # for testing query param injection
        if query_params.get('name'):
            query_params.add('filter{metaData__asset__name}', query_params.get('name'))
        return super(UserViewSet, self).list(request, *args, **kwargs)

class GroupViewSet(DynamicModelViewSet):
    features = (
        DynamicModelViewSet.INCLUDE, DynamicModelViewSet.EXCLUDE,
        DynamicModelViewSet.FILTER, DynamicModelViewSet.SORT,
        DynamicModelViewSet.SIDELOADING, DynamicModelViewSet.DEBUG
    )
    model = Group
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    lookup_field = 'uid'


class LocationViewSet(DynamicModelViewSet):
    features = (
        DynamicModelViewSet.INCLUDE, DynamicModelViewSet.EXCLUDE,
        DynamicModelViewSet.FILTER, DynamicModelViewSet.SORT,
        DynamicModelViewSet.SIDELOADING, DynamicModelViewSet.DEBUG
    )
    model = Location
    serializer_class = LocationSerializer
    queryset = Location.objects.all()
    lookup_field = 'uid'


