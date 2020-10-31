"""endorsity URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.views.generic.base import RedirectView

from allauth.socialaccount import providers
from importlib import import_module


urlpatterns = [
    path('SVqekyep318CwgdxLFDxG5YUuOJZEUI0uaJYkePvAgbHejIa3cKLbyQ/', admin.site.urls), # ramdom string for security reasons
    path('socialaccount/signup/', RedirectView.as_view(url=reverse_lazy('accounts:account_exists')), name='socialaccount_signup'),
    path('brand/', include('brand.urls')),
    path('influencer/', include('influencer.urls')),
    path("notifications/", include('notifications.urls')),
    path('', include('accounts.urls', namespace='accounts')),
]

handler404 = 'accounts.views.handler404'
handler500 = 'accounts.views.handler500'
handler403 = 'accounts.views.handler403'
handler400 = 'accounts.views.handler400'


provider_urlpatterns = []
for provider in providers.registry.get_list():
    try:
        prov_mod = import_module(provider.get_package() + '.urls')
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, 'urlpatterns', None)
    if prov_urlpatterns:
        provider_urlpatterns += prov_urlpatterns
urlpatterns += provider_urlpatterns

urlpatterns += (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) +
                static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))
