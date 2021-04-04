from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class IllegalDateError(Exception):
    """Exception raised for errors in the input date.

    Attributes:
        date_str -- input date which caused the error
        message -- explanation of the error
    """

    def __init__(
        self, date_str, message="Date should be in '%Y-%m' format in acceptable ranges"
    ):
        self.date_str = date_str
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.date_str} -> {self.message}"


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, IllegalDateError):
        return Response({"error": exc.message}, status=status.HTTP_400_BAD_REQUEST)

    return response
