from common.utils import from_year_month_to_datetime
from django.db.models import Avg, CharField, Count, F, Max, Value, Window
from django.db.models.functions import (
    Concat,
    ExtractMonth,
    ExtractYear,
    Floor,
    Ntile,
    Round,
)
from django_cte import With
import rest_framework
from rest_framework import generics

from .models import Property
from .serializers import AvgPriceSerializer, TransactionCountSerializer

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    extend_schema_serializer,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers


MAX_BIN_COUNT = 8
DECIMAL_PLACES = 100
LOWER_OUTLIER_BOUNDARY = 0.05
UPPER_OUTLIER_BOUNDARY = 0.95


@extend_schema(
    description="Average property price over time",
    parameters=[
        OpenApiParameter(
            name="postal_code",
            type=str,
            description="Filter by postal code",
            required=False,
            examples=[
                OpenApiExample(
                    "Example 1",
                    summary="LS7 1NJ",
                    description="Postal code : LS7 1NJ",
                    value="LS7 1NJ",
                ),
                OpenApiExample(
                    "Example 2",
                    summary="SE1 7GU",
                    description="Postal code : SE1 7GU",
                    value="SE1 7GU",
                ),
            ],
        ),
        OpenApiParameter(
            name="from",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description="Start of the date range (inclusive). Date format is 'Y-m' e.g. 2010-11.<br>"
            "<b>Also note that this optional parameter does not work without parameter 'to'</b>.",
            required=False,
            examples=[
                OpenApiExample(
                    "Example 1",
                    summary="2012-11",
                    description="Start from November 2012",
                    value="2012-11",
                ),
                OpenApiExample(
                    "Example 2",
                    summary="2020-05",
                    description="Start from May 2020",
                    value="2020-05",
                ),
            ],
        ),
        OpenApiParameter(
            name="to",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description="End of the date range (inclusive). Date format is 'Y-m' e.g. 2012-11.<br>"
            "<b>Also note that this optional parameter does not work without parameter 'from'</b>.",
            required=False,
            examples=[
                OpenApiExample(
                    "Example 1",
                    summary="2021-02",
                    description="Until end of February 2021",
                    value="2021-02",
                ),
                OpenApiExample(
                    "Example 2",
                    summary="2020-12",
                    description="Until end of December 2020",
                    value="2020-12",
                ),
            ],
        ),
    ],
    responses={
        200: AvgPriceSerializer,
        400: extend_schema_serializer(
            many=False,
            examples=[
                OpenApiExample(
                    "Invalid Request",
                    value={
                        "error": "Date should be in '%Y-%m' format in acceptable ranges"
                    },
                    status_codes=["400"],
                )
            ],
        )(inline_serializer("Error400", {"string": serializers.CharField()})),
    },
)
class PropertyAveragePriceList(generics.ListAPIView):
    serializer_class = AvgPriceSerializer

    def get_queryset(self):
        queryset = Property.objects.all()
        postal_code = self.request.query_params.get("postal_code")
        if postal_code is not None:
            queryset = queryset.filter(postal_code=postal_code)

        start = self.request.query_params.get("from")
        end = self.request.query_params.get("to")

        if start is not None and end is not None:
            start_date = from_year_month_to_datetime(start)
            end_date = from_year_month_to_datetime(end, last_day=True)
            queryset = queryset.filter(transfer_date__range=[start_date, end_date])

        queryset = (
            queryset.annotate(
                month=ExtractMonth("transfer_date"), year=ExtractYear("transfer_date")
            )
            .filter(property_type__in=["T", "D", "S", "F"])
            .values("property_type", "month", "year")
            .annotate(avg_price=Avg("price"))
            .order_by("year", "month")
        )

        return queryset


@extend_schema(
    description="Number of transactions over time",
    parameters=[
        OpenApiParameter(
            name="postal_code",
            type=str,
            description="Filter by postal code",
            required=False,
            examples=[
                OpenApiExample(
                    "Example 1",
                    summary="L3 0AZ",
                    description="Postal code : LS7 1NJ",
                    value="L3 0AZ",
                ),
                OpenApiExample(
                    "Example 2",
                    summary="LE1 6AU",
                    description="Postal code : LE1 6AU",
                    value="LE1 6AU",
                ),
            ],
        ),
        OpenApiParameter(
            name="date",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description="Transaction date. Date format is 'Y-m' e.g. 2010-11.<br>",
            required=False,
            examples=[
                OpenApiExample(
                    "Example 1",
                    summary="2012-11",
                    description="Transaction date is November 2012",
                    value="2012-11",
                ),
                OpenApiExample(
                    "Example 2",
                    summary="2020-05",
                    description="Transaction date is May 2020",
                    value="2020-05",
                ),
            ],
        ),
    ],
    responses={
        200: AvgPriceSerializer,
        400: extend_schema_serializer(
            many=False,
            examples=[
                OpenApiExample(
                    "Invalid Request",
                    value={
                        "error": "Date should be in '%Y-%m' format in acceptable ranges"
                    },
                    status_codes=["400"],
                )
            ],
        )(inline_serializer("Error400", {"string": serializers.CharField()})),
    },
)
class PropertyTransactionCountList(generics.ListAPIView):
    serializer_class = TransactionCountSerializer

    def get_queryset(self):
        queryset = Property.objects.all()
        postal_code = self.request.query_params.get("postal_code")
        if postal_code is not None:
            queryset = queryset.filter(postal_code=postal_code)

        date = self.request.query_params.get("date")

        if date is not None:
            start_date = from_year_month_to_datetime(date)
            end_date = from_year_month_to_datetime(date, last_day=True)
            queryset = queryset.filter(transfer_date__range=[start_date, end_date])

        # check if queryset is empyty
        if not queryset:
            return queryset.none()

        queryset_count = queryset.count()
        
        normal_range_start = int(LOWER_OUTLIER_BOUNDARY * queryset_count)
        normal_range_end = int(UPPER_OUTLIER_BOUNDARY * queryset_count)

        quartiles_cte = With(
            queryset.annotate(
                price_quartile=Window(
                    expression=Ntile(num_buckets=queryset_count),
                    order_by=F("price").asc(),
                )
            ).values("price", "price_quartile")
        )
        iqr = (
            quartiles_cte.queryset()
            .with_cte(quartiles_cte)
            .values("price_quartile")
            .filter(price_quartile__in=[normal_range_start, normal_range_end])
            .annotate(quartile_break=Max("price"))
            .order_by("price_quartile")
        )

        # return empty queryset if there is no interquartile values.
        if len(iqr) != 2:
            return queryset.none()

        min_price = iqr[0]["quartile_break"]
        max_price = iqr[1]["quartile_break"]
        bin_width = (max_price - min_price) / (MAX_BIN_COUNT - 1)
        bin_width = (
            int(bin_width / DECIMAL_PLACES) * DECIMAL_PLACES
        )  # truncate to nearest decimal places

        bins_cte = With(
            queryset.annotate(bin_floor=Floor(F("price") / bin_width) * bin_width)
            .values("bin_floor")
            .filter(price__gte=min_price, price__lte=max_price)
            .order_by("bin_floor")
            .annotate(count=Count("id"))
        )
        queryset = (
            bins_cte.queryset()
            .with_cte(bins_cte)
            .values("bin_floor", "count")
            .annotate(
                bin_range=Concat(
                    Value("£"),
                    Round(F("bin_floor") / 1000),
                    Value("k"),
                    Value(" - "),
                    Value("£"),
                    Round((F("bin_floor") + bin_width) / 1000),
                    Value("k"),
                    output_field=CharField(),
                )
            )
            .order_by("bin_floor")
        )

        return queryset


