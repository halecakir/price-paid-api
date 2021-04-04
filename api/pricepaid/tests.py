import datetime
import math
import random
from collections import defaultdict
from operator import itemgetter

from django.test import TestCase

from .models import Property

# Set seed for pseudo random number
random.seed(10)

MAX_BIN_COUNT = 8
DECIMAL_PLACES = 2
LOWER_OUTLIER_BOUNDARY = 0.05
UPPER_OUTLIER_BOUNDARY = 0.95
THOUSAND2K = 1000

# TEST_SAMPLE_COUNT == 0 -> empty database
TEST_SAMPLE_COUNT = 10000
# Sample year range size
TEST_YEAR_RANGE_SIZE = 1


def random_date_generate(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + datetime.timedelta(days=random_number_of_days)
    return random_date


class BaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Generates n (i.e. TEST_SAMPLE_COUNT) number of test sample.
        """
        cls.year, cls.month, cls.day = 2020, 5, 1
        start_date = datetime.date(cls.year, cls.month, cls.day)
        end_date = datetime.date(cls.year + TEST_YEAR_RANGE_SIZE, cls.month, cls.day)

        cls.post_codes = ["MK18 5JF", "CM9 6UR", "BS23 2QX", "HP13 6YB"]

        cls.property_types = ["T", "D", "S", "F"]

        price_range = (50000, 1000000)

        cls.data = []
        for _ in range(TEST_SAMPLE_COUNT):
            random_date = random_date_generate(start_date, end_date)
            property = Property.objects.create(
                postal_code=random.choice(cls.post_codes),
                property_type=random.choice(cls.property_types),
                price=random.randint(price_range[0], price_range[1]),
                transfer_date=random_date,
            )
            cls.data.append(property.__dict__)


class AveragePriceTest(BaseTest):
    def test_invalid_date_format(self):
        invalid_format_params = {"from": "2015/10", "to": "2015-12"}

        response = self.client.get(
            "/api/v1/properties/avg_prices", invalid_format_params
        )

        error_message = "Date should be in '%Y-%m' format in acceptable ranges"
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), error_message)

    def test_invalid_date_format_with_day(self):
        invalid_format_params = {"from": "2015-10-12", "to": "2015-12"}

        response = self.client.get(
            "/api/v1/properties/avg_prices", invalid_format_params
        )

        error_message = "Date should be in '%Y-%m' format in acceptable ranges"
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), error_message)

    def test_invalid_month(self):
        invalid_month_params = {"from": "2015-13", "to": "2015-12"}

        response = self.client.get(
            "/api/v1/properties/avg_prices", invalid_month_params
        )

        error_message = "Date should be in '%Y-%m' format in acceptable ranges"
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), error_message)

    def test_average_prices(self):
        start_year, end_year = self.year, self.year + 1
        start_month, end_month = self.month, self.month
        start_day, end_day = 1, 1
        postal_code = random.choice(self.post_codes)
        params = {
            "from": f"{start_year}-{start_month}",
            "to": f"{end_year}-{end_month}",
            "postal_code": postal_code,
        }

        response = self.client.get("/api/v1/properties/avg_prices", params)
        start_date = datetime.date(start_year, start_month, start_day)
        end_date = datetime.date(end_year, end_month, end_day)

        # {"property_type" : {"year" : {"month"  : float}}}
        expected_avg_prices = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        for item in self.data:
            if item["postal_code"] == postal_code:
                if start_date <= item["transfer_date"] <= end_date:
                    pt = item["property_type"]
                    year = item["transfer_date"].year
                    month = item["transfer_date"].month
                    price = item["price"]
                    expected_avg_prices[pt][year][month].append(price)

        def avg(lst):
            return round(sum(lst) / len(lst), 2)

        for item in response.data:
            pt = item["property_type"]
            year = item["year"]
            month = item["month"]
            avg_price = item["avg_price"]

            self.assertEqual(
                float(avg_price), avg(expected_avg_prices[pt][year][month])
            )


class TransactionCountTest(BaseTest):
    def test_invalid_date_format(self):
        invalid_format_params = {"date": "2015/10"}

        response = self.client.get(
            "/api/v1/properties/count_transactions", invalid_format_params
        )

        error_message = "Date should be in '%Y-%m' format in acceptable ranges"
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), error_message)

    def test_invalid_date_format_with_day(self):
        invalid_format_params = {"date": "2015-10-12"}

        response = self.client.get(
            "/api/v1/properties/count_transactions", invalid_format_params
        )

        error_message = "Date should be in '%Y-%m' format in acceptable ranges"
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), error_message)

    def test_invalid_month(self):
        invalid_month_params = {"date": "2015-13"}

        response = self.client.get(
            "/api/v1/properties/count_transactions", invalid_month_params
        )

        error_message = "Date should be in '%Y-%m' format in acceptable ranges"
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), error_message)

    def test_count_transactions(self):
        year = self.year
        month = self.month
        postal_code = random.choice(self.post_codes)
        params = {
            "date": f"{year}-{month}",
            "postal_code": postal_code,
        }

        response = self.client.get("/api/v1/properties/count_transactions", params)

        filtered_set = []

        for item in self.data:
            if item["postal_code"] == postal_code:
                if (
                    year == item["transfer_date"].year
                    and month == item["transfer_date"].month
                ):
                    filtered_set.append(item)

        count = len(filtered_set)
        if count == 0:
            self.assertEqual(response.data, [])
            return

        normal_range_start = math.ceil(LOWER_OUTLIER_BOUNDARY * count)
        normal_range_end = math.ceil(UPPER_OUTLIER_BOUNDARY * count)
        filtered_set = sorted(filtered_set, key=itemgetter("price"))

        min_price = filtered_set[normal_range_start - 1]["price"]
        max_price = filtered_set[normal_range_end - 1]["price"]

        bin_width = (max_price - min_price) / (MAX_BIN_COUNT - 1)
        mask_digit = pow(10, DECIMAL_PLACES)
        bin_width = math.ceil(bin_width / mask_digit) * mask_digit
        bin_width = 1 if bin_width == 0 else bin_width

        bin_counts = defaultdict(int)
        for item in filtered_set:
            if item["price"] > max_price:
                bin_floor = int(max_price / bin_width) * bin_width
            else:
                bin_floor = int(item["price"] / bin_width) * bin_width
            bin_counts[bin_floor] += 1

        bins = sorted(bin_counts.items(), key=lambda item: item[0])

        for expected, actual in zip(bins, response.data):
            bin_start = expected[0] // THOUSAND2K
            bin_end = (expected[0] + bin_width) // THOUSAND2K
            expected_count = expected[1]
            expected_bin_range = f"£{bin_start}k - £{bin_end}k"

            self.assertEqual(expected_bin_range, actual["bin_range"])
            self.assertEqual(expected_count, actual["bin_size"])
