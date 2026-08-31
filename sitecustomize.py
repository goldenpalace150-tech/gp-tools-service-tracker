"""Startup safety for Streamlit Google Sheets.

No credentials are stored in this repository.  This module prevents a malformed
Google service-account secret from crashing the entire Streamlit app before the
login screen appears.
"""

try:
    import streamlit as _st

    _original_st_connection = _st.connection

    class _UnavailableConnection:
        def __init__(self, error):
            self.error = error

        def read(self, *args, **kwargs):
            raise RuntimeError(
                "HTTPError: Google Sheets credentials are invalid or unavailable."
            )

        def update(self, *args, **kwargs):
            raise RuntimeError(
                "HTTPError: Google Sheets credentials are invalid; data was NOT saved."
            )

        def clear(self, *args, **kwargs):
            raise RuntimeError(
                "HTTPError: Google Sheets credentials are invalid; data was NOT changed."
            )

    def _safe_connection(*args, **kwargs):
        try:
            return _original_st_connection(*args, **kwargs)
        except (ValueError, TypeError, KeyError) as exc:
            return _UnavailableConnection(exc)

    _st.connection = _safe_connection
except Exception:
    pass
