from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # ─── Admin Django ────────────────────────────────────────────────────────
    path('admin/', admin.site.urls),
    
    # ─── Documentação API (Swagger/OpenAPI) ───────────────────────────────────
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # ─── API REST v1 ─────────────────────────────────────────────────────────
    path('api/v1/', include('escola_musica.urls')),
    
    # ─── Rotas legadas (temporário, serão removidas após migração completa) ────
    path('', include('escola_musica.urls')),
]