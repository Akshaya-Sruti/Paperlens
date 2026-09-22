"""Domain exceptions for PDF processing.

Routes translate these into HTTP responses with human-readable
messages. Internal details never leak to the frontend.
"""


class PdfError(Exception):
    """Base class for PDF processing failures."""

    user_message = "Unable to process this PDF."


class PasswordProtectedPdfError(PdfError):
    user_message = (
        "This PDF is password-protected. Please upload an unlocked copy."
    )


class CorruptedPdfError(PdfError):
    user_message = (
        "This file appears to be corrupted or is not a valid PDF. "
        "Try another file."
    )


class EmptyPdfError(PdfError):
    user_message = "This PDF contains no pages. Try another file."


class ExtractionError(PdfError):
    user_message = (
        "Something went wrong while reading this PDF. Try another file."
    )
