"""Runtime compatibility and startup safety for Streamlit Google Sheets.

No credentials are stored here.  The code only normalizes the private key that
Streamlit supplies at runtime.  Some TOML edits leave escaped newlines, extra
quotes, or irregular wrapping in a PEM key; google-auth requires exact PEM
formatting.

If credentials are still unusable, the app is allowed to start with an
unavailable Google Sheets client instead of crashing before the login screen.
Reads will then fail through the application's normal connection-error path.
"""

import re
import textwrap


def _rebuild_private_key(value):
    if not isinstance(value, str) or not value.strip():
        return value

    key = value.strip()

    # Remove accidental outer quoting from copy/paste and normalize escaped
    # newline forms that may survive TOML parsing.
    if (key.startswith('"') and key.endswith('"')) or (
        key.startswith("'") and key.endswith("'")
    ):
        key = key[1:-1].strip()
    key = key.replace("\\r\\n", "\n")
    key = key.replace("\\n", "\n")
    key = key.replace("\\r", "\n")
    key = key.replace("\r\n", "\n").replace("\r", "\n")

    begin = "-----BEGIN PRIVATE KEY-----"
    end = "-----END PRIVATE KEY-----"
    begin_pos = key.find(begin)
    end_pos = key.find(end)

    if begin_pos >= 0 and end_pos > begin_pos:
        body = key[begin_pos + len(begin):end_pos]
        # A PEM body is base64.  Rebuilding from the base64 characters removes
        # spaces, indentation, pasted line wrapping, and other harmless noise.
        body = re.sub(r"[^A-Za-z0-9+/=]", "", body)
        if body:
            wrapped = "\n".join(textwrap.wrap(body, 64))
            return f"{begin}\n{wrapped}\n{end}\n"

    # If the markers were not found, preserve the normalized value so
    # google-auth can raise the real validation error.
    if key and not key.endswith("\n"):
        key += "\n"
    return key


try:
    import gspread
    from gspread import auth as _gspread_auth

    _original_service_account_from_dict = _gspread_auth.service_account_from_dict

    def _normalize_service_account_info(info):
        if not isinstance(info, dict):
            return info
        normalized = dict(info)
        if "private_key" in normalized:
            normalized["private_key"] = _rebuild_private_key(
                normalized.get("private_key")
            )
        return normalized

    def _patched_service_account_from_dict(info, *args, **kwargs):
        return _original_service_account_from_dict(
            _normalize_service_account_info(info), *args, **kwargs
        )

    _gspread_auth.service_account_from_dict = _patched_service_account_from_dict
    gspread.service_account_from_dict = _patched_service_account_from_dict
except Exception:
    pass


# Safety net: never let a malformed Google credential prevent the ERP itself
# from opening.  If connection construction fails, return a small unavailable
# client.  The application's get_doctype() already handles read failures and
# presents empty data instead of terminating the process.
try:
    from streamlit_gsheets import GSheetsConnection

    _original_gsheets_connect = GSheetsConnection._connect

    class _UnavailableGSheetsClient:
        def __init__(self, error):
            self.error = error

        def read(self, *args, **kwargs):
            raise RuntimeError(
                "HTTPError: Google Sheets credentials are invalid or unavailable. "
                f"Original error: {type(self.error).__name__}"
            )

        def update(self, *args, **kwargs):
            raise RuntimeError(
                "HTTPError: Google Sheets credentials are invalid; data was NOT saved. "
                f"Original error: {type(self.error).__name__}"
            )

        def clear(self, *args, **kwargs):
            raise RuntimeError(
                "HTTPError: Google Sheets credentials are invalid; data was NOT changed."
            )

    def _safe_gsheets_connect(self, **kwargs):
        try:
            return _original_gsheets_connect(self, **kwargs)
        except (ValueError, TypeError, KeyError) as exc:
            return _UnavailableGSheetsClient(exc)

    GSheetsConnection._connect = _safe_gsheets_connect
except Exception:
    pass
