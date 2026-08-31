"""Runtime compatibility patch for service-account keys stored in TOML secrets.

Streamlit deployments may end up exposing a PEM private key with literal ``\\n``
sequences rather than real line breaks.  gspread/google-auth requires a normal
PEM string.  Python imports ``sitecustomize`` automatically at interpreter
startup, so normalize the credential dictionary before st-gsheets-connection
uses it.  No credentials are stored in this repository.
"""

try:
    import gspread
    from gspread import auth as _gspread_auth

    _original_service_account_from_dict = _gspread_auth.service_account_from_dict

    def _normalize_service_account_info(info):
        if not isinstance(info, dict):
            return info

        normalized = dict(info)
        private_key = normalized.get("private_key")
        if isinstance(private_key, str) and private_key:
            private_key = private_key.strip()
            private_key = private_key.replace("\\r\\n", "\n")
            private_key = private_key.replace("\\n", "\n")
            private_key = private_key.replace("\r\n", "\n").replace("\r", "\n")
            if private_key and not private_key.endswith("\n"):
                private_key += "\n"
            normalized["private_key"] = private_key
        return normalized

    def _patched_service_account_from_dict(info, *args, **kwargs):
        return _original_service_account_from_dict(
            _normalize_service_account_info(info), *args, **kwargs
        )

    # st-gsheets-connection imports this helper from gspread, so patch both
    # public locations before the application imports streamlit_gsheets.
    _gspread_auth.service_account_from_dict = _patched_service_account_from_dict
    gspread.service_account_from_dict = _patched_service_account_from_dict
except Exception:
    # Never stop the application from starting merely because the optional
    # compatibility patch could not be loaded.
    pass
