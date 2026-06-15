from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # API REST (JWT)
    path("api/", include("marketplace.api_urls")),
    path("api/", include("addons.urls")),
    # Vues Django classiques (templates HTML)
    path("", include("marketplace.urls")),
    path('api/messaging/',       include('messaging.urls')),
    path('api/administration/',  include('administration.urls')),
    path('api/chatbot/',         include('chatbot.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

