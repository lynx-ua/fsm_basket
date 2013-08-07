from django.conf.urls import patterns, include, url
from basket.views import IndexPage, AddToBasket, DeleteFromBasket, CleanBasket
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', IndexPage.as_view(), name='index-page'),
    url(r'^add/(?P<code>\w+)/$', AddToBasket.as_view(), name='add-to-basket'),
    url(r'^delete/(?P<code>\w+)/$', DeleteFromBasket.as_view(), name='delete-from-basket'),
    url(r'^clean/$', CleanBasket.as_view(), name='clean-basket'),
    url(r'^admin/', include(admin.site.urls)),
)
