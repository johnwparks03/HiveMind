"""Validation and text encoding for pgvector values. The Lambdas have no pgvector adapter or numpy, so
a vector travels as a text literal such as '[0.1,0.2]' and is cast in SQL with `%s::vector`."""
import math
import os


def embedding_dimension():
    return int(os.environ.get("EMBEDDING_DIMENSION", "384"))


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value):
    """A finite int or float. bool is excluded, and so are NaN and inf (json.loads accepts them)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def is_embedding(values, dimension=None):
    """A list of exactly `dimension` (default EMBEDDING_DIMENSION) finite numbers."""
    dimension = embedding_dimension() if dimension is None else dimension
    return isinstance(values, list) and len(values) == dimension and all(is_number(x) for x in values)


def vector_literal(values):
    return "[" + ",".join(repr(float(x)) for x in values) + "]"
