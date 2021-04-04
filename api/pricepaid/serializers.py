from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Valid example 1",
            summary="Flat 2019-03",
            description="The average Flat price in March 2019 is 73776.46£.",
            value={
                "property_type": "F",
                "year": 2019,
                "month": 3,
                "avg_price": "73776.46",
            },
            request_only=False,
            response_only=True,
        ),
    ]
)
class AvgPriceSerializer(serializers.Serializer):
    property_type = serializers.CharField(max_length=1)
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    avg_price = serializers.DecimalField(max_digits=12, decimal_places=2)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Valid example 1",
            summary="Flat 2019-03",
            description="The average Flat price in March 2019 is 73776.46£.",
            value={
                "bin_range": "F",
                "count": 2019
            },
            request_only=False,
            response_only=True,
        ),
    ]
)
class TransactionCountSerializer(serializers.Serializer):
    bin_range = serializers.CharField(max_length=30)
    count = serializers.IntegerField()
