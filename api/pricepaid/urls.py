from django.urls import path

from .views import PropertyAveragePriceList, PropertyTransactionCountList

urlpatterns = [
    path("properties/avg_prices", PropertyAveragePriceList.as_view()),
    path("properties/count_transactions", PropertyTransactionCountList.as_view()),
]
