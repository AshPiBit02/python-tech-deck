"""
PROBLEM: You're building a generic "filter records" endpoint where the allowed
filter fields vary (e.g. ?state=active&country=Nepal&min_price=233) and you don't
want ot hardcode every possible query parameter as a funtion argument - new filter-
-able fields get added to the data model constantly.

SOLUTION: Take the Request object and read request.query_params directly (a case-
-sensitive, mutli-dict of everything in the URL's query string) instead of declaring
each one individually.
"""

from fastapi import FastAPI,Request

app=FastAPI(title="Dynamic Query Params Demo")

RECORDS=[
    {"id":1,"status":"active","country":"Nepal","price":899},
    {"id":2,"status":"active","country":"Germany","price":36},
    {"id":3,"status":"inactive","country":"US","price":56},
    {"id":4,"status":"active","country":"Demmark","price":263},
]

FILTERABLE_FIELDS={"status","country"}
