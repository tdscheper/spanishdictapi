"""SpanishDictAPI development configuration."""

import pathlib

SPANISHDICTAPI_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATABASE_FILENAME = SPANISHDICTAPI_ROOT/'var'/'spanishdictapi.sqlite3'

JSON_AS_ASCII = False
JSON_SORT_KEYS = False
