"""Tests for OutputFormatter — focuses on the plain-format flattening
regression and parseable json/yaml output."""

import io
import json

import yaml
from rich.console import Console

from jctl.utils.output import OutputFormatter, format_duration


def _format(data, fmt: str) -> str:
    """Render data to a string using OutputFormatter."""
    buf = io.StringIO()
    OutputFormatter(Console(file=buf, width=200, force_terminal=False)).format(data, fmt)
    return buf.getvalue()


class TestFormatPlain:
    def test_flat_dict(self):
        out = _format({"a": 1, "b": "two"}, "plain")
        assert "a=1" in out
        assert "b=two" in out

    def test_nested_dict_uses_dot_path(self):
        out = _format({"outer": {"inner": "v"}}, "plain")
        assert "outer.inner=v" in out

    def test_list_of_scalars_joined_by_comma(self):
        out = _format({"scopes": ["a", "b", "c"]}, "plain")
        assert "scopes=a,b,c" in out

    def test_list_of_dicts_uses_index_notation(self):
        """The bug was: ['stages' key with list of dicts] dumped raw repr()."""
        out = _format(
            {"stages": [{"name": "Build", "status": "OK"}, {"name": "Test", "status": "OK"}]},
            "plain",
        )
        assert "stages[0].name=Build" in out
        assert "stages[1].status=OK" in out
        # No raw Python dict repr leaking through
        assert "{'name'" not in out


class TestFormatJsonYaml:
    def test_json_is_parsable(self):
        out = _format({"a": 1, "nested": {"b": 2}}, "json")
        # Rich's print_json adds a trailing newline; just ensure round-trip works.
        assert json.loads(out)["nested"]["b"] == 2

    def test_yaml_is_parsable(self):
        out = _format({"a": 1, "nested": {"b": 2}}, "yaml")
        assert yaml.safe_load(out)["nested"]["b"] == 2


class TestFormatDuration:
    def test_negative_is_n_a(self):
        assert format_duration(-1) == "N/A"

    def test_sub_second_shows_milliseconds(self):
        # Was the bug: 228ms floored to "0s". Pipeline stages routinely
        # execute in <1s — those rows looked like no-ops.
        assert format_duration(228) == "228ms"
        assert format_duration(0) == "0ms"
        assert format_duration(999) == "999ms"

    def test_one_second_boundary(self):
        assert format_duration(1000) == "1s"
        assert format_duration(1500) == "1s"  # truncates within seconds

    def test_minutes_and_seconds(self):
        assert format_duration(90_000) == "1m 30s"
        assert format_duration(60_000) == "1m"

    def test_hours_and_minutes(self):
        assert format_duration(3_660_000) == "1h 1m"
        assert format_duration(3_600_000) == "1h"

    def test_days_and_hours(self):
        # 25h = 1d 1h
        assert format_duration(25 * 3_600_000) == "1d 1h"
