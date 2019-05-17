from django.conf.urls import url

from user.views import RegisterView, ActivateView, LoginView, UserInfoView, UserOrderView, AddressView, LogoutView

urlpatterns = [
    # url(r'^register/$', views.register, name='register'),
    url(r'^register/$', RegisterView.as_view(), name='register'),
    url(r'^activate/(?P<token>.*)$', ActivateView.as_view(), name='activate'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url(r'^$', UserInfoView.as_view(), name='info'),
    url(r'^order/$', UserOrderView.as_view(), name='order'),
    url(r'^address/$', AddressView.as_view(), name='address'),

]
