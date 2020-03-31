from django.conf.urls import include, url

from dynamic_rest.routers import DynamicRouter
from dapp1 import views
from django.contrib import admin


router = DynamicRouter()
#router.register_resource(views.UserViewSet)
#router.register_resource(views.GroupViewSet)
#router.register_resource(views.LocationViewSet)

router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'location', views.LocationViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url('admin/', admin.site.urls)
]

urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]

