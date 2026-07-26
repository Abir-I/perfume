from django.urls import path

from .views import AddCartItemView, CartItemDetailView, CartView

urlpatterns = [
    path('', CartView.as_view()),                                   # GET    /api/cart/
    path('add/', AddCartItemView.as_view()),                        # POST   /api/cart/add/
    path('items/', AddCartItemView.as_view()),                      # kept as an alias for backward compatibility
    path('remove/<int:cart_item_id>/', CartItemDetailView.as_view()),  # DELETE /api/cart/remove/{id}/
    path('update/<int:cart_item_id>/', CartItemDetailView.as_view()),  # PATCH  /api/cart/update/{id}/
]
