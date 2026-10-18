import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

from common import vectors  # noqa: E402


@pytest.mark.parametrize("value,expected", [(1, True), (0, True), (-3, True), (True, False), (1.0, False),
                                            ("1", False), (None, False)])
def test_is_int_rejects_bool_and_non_ints(value, expected):
    assert vectors.is_int(value) is expected


@pytest.mark.parametrize("value,expected", [(1, True), (0.5, True), (-2.5, True), (True, False),
                                            (float("nan"), False), (float("inf"), False),
                                            (float("-inf"), False), ("0.1", False), (None, False)])
def test_is_number_requires_a_finite_non_bool_number(value, expected):
    assert vectors.is_number(value) is expected


def test_is_embedding_checks_type_length_and_elements(monkeypatch):
    monkeypatch.delenv("EMBEDDING_DIMENSION", raising=False)
    assert vectors.is_embedding([0.1] * 384)
    assert not vectors.is_embedding([0.1] * 383) and not vectors.is_embedding("x" * 384)
    assert not vectors.is_embedding([0.1] * 383 + [float("nan")])
    assert vectors.is_embedding([1, 2, 3], dimension=3) and not vectors.is_embedding((1, 2, 3), dimension=3)
    monkeypatch.setenv("EMBEDDING_DIMENSION", "2")
    assert vectors.is_embedding([0.1, 0.2]) and vectors.embedding_dimension() == 2


def test_vector_literal_is_a_bracketed_comma_list_that_round_trips_floats():
    assert vectors.vector_literal([1, 0.5, -2.25]) == "[1.0,0.5,-2.25]"
    assert vectors.vector_literal([1e-05]) == "[1e-05]"
