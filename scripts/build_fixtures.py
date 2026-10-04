"""Rebuild fixtures/tasks from the definitions below.

Each task is a tiny pure-Python package with a real bug class. The script writes the base
snapshot, derives the gold patch and test patch with unified diffs, builds the submission
library, then derives FAIL_TO_PASS / PASS_TO_PASS by running the tests (fail at base and pass
with the gold patch, or pass in both), the way SWE-bench does. Run with `make fixtures`.
"""

from __future__ import annotations

import difflib
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from patchbench.executors.local import LocalExecutor  # noqa: E402
from patchbench.models import Task  # noqa: E402
from patchbench.runner import execute  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "tasks"


@dataclass
class Spec:
    slug: str
    package: str
    issue: str
    base: str
    fixed: str
    regression: str
    base_tests: str
    new_tests: str
    partial: str | None = None


SPECS = [
    Spec(
        slug="slugify-1",
        package="textkit_slug",
        issue="slugify() drops accented letters instead of transliterating them: "
        "slugify('Café Münster') returns 'caf-m-nster', expected 'cafe-munster'.",
        base='''"""Turn titles into URL slugs."""

import re


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")
''',
        fixed='''"""Turn titles into URL slugs."""

import re
import unicodedata


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")
''',
        regression='''"""Turn titles into URL slugs."""

import re
import unicodedata


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]", "-", text)
    return text.strip("-")
''',
        base_tests="""from textkit_slug import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"


def test_trims_and_collapses():
    assert slugify("  a   b  ") == "a-b"


def test_symbols():
    assert slugify("rock & roll!") == "rock-roll"
""",
        new_tests="""

def test_accents_are_transliterated():
    assert slugify("Café Münster") == "cafe-munster"
""",
    ),
    Spec(
        slug="paginate-1",
        package="listkit_page",
        issue="paginate() drops the last item of every page: paginate(list(range(10)), 1, 3) "
        "returns [0, 1] instead of [0, 1, 2].",
        base='''"""Slice a list into 1-based pages."""


def paginate(items: list, page: int, per_page: int) -> list:
    start = (page - 1) * per_page
    end = start + per_page - 1
    return items[start:end]
''',
        fixed='''"""Slice a list into 1-based pages."""


def paginate(items: list, page: int, per_page: int) -> list:
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]
''',
        regression='''"""Slice a list into 1-based pages."""


def paginate(items: list, page: int, per_page: int) -> list:
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end] or items[:per_page]
''',
        base_tests="""from listkit_page import paginate


def test_empty_list():
    assert paginate([], 1, 3) == []


def test_page_past_the_end_is_empty():
    assert paginate(list(range(4)), 9, 3) == []
""",
        new_tests="""

def test_full_page():
    assert paginate(list(range(10)), 1, 3) == [0, 1, 2]


def test_last_page_is_short():
    assert paginate(list(range(10)), 4, 3) == [9]
""",
    ),
    Spec(
        slug="headers-1",
        package="httpkit_headers",
        issue="Headers lookups are case sensitive: after Headers({'Content-Type': 'x'}), "
        "get('content-type') returns None. HTTP header names are case insensitive.",
        base='''"""A tiny HTTP header container."""


class Headers:
    def __init__(self, items=None):
        self._items = dict(items or {})

    def get(self, name, default=None):
        return self._items.get(name, default)

    def __contains__(self, name):
        return name in self._items

    def set(self, name, value):
        self._items[name] = value
''',
        fixed='''"""A tiny HTTP header container."""


class Headers:
    def __init__(self, items=None):
        self._items = {k.lower(): v for k, v in (items or {}).items()}

    def get(self, name, default=None):
        return self._items.get(name.lower(), default)

    def __contains__(self, name):
        return name.lower() in self._items

    def set(self, name, value):
        self._items[name.lower()] = value
''',
        regression='''"""A tiny HTTP header container."""


class Headers:
    def __init__(self, items=None):
        self._items = {k.lower(): v for k, v in (items or {}).items()}

    def get(self, name, default=None):
        return self._items.get(name.lower())

    def __contains__(self, name):
        return name.lower() in self._items

    def set(self, name, value):
        self._items[name.lower()] = value
''',
        base_tests="""from httpkit_headers import Headers


def test_get_exact_name():
    assert Headers({"Accept": "a"}).get("Accept") == "a"


def test_missing_returns_default():
    assert Headers().get("X-Nope", "d") == "d"


def test_set_then_get():
    h = Headers()
    h.set("Host", "example.org")
    assert h.get("Host") == "example.org"
""",
        new_tests="""

def test_get_is_case_insensitive():
    assert Headers({"Content-Type": "x"}).get("content-type") == "x"


def test_contains_is_case_insensitive():
    assert "ACCEPT" in Headers({"Accept": "a"})
""",
    ),
    Spec(
        slug="duration-1",
        package="timekit_duration",
        issue="parse_duration('5m') returns 5 instead of 300: minutes are treated as seconds.",
        base='''"""Parse durations such as '1h30m' into seconds."""

import re

UNITS = {"s": 1, "m": 1, "h": 3600}


def parse_duration(text: str) -> int:
    total = 0
    for amount, unit in re.findall(r"(\\d+)([smh])", text):
        total += int(amount) * UNITS[unit]
    return total
''',
        fixed='''"""Parse durations such as '1h30m' into seconds."""

import re

UNITS = {"s": 1, "m": 60, "h": 3600}


def parse_duration(text: str) -> int:
    total = 0
    for amount, unit in re.findall(r"(\\d+)([smh])", text):
        total += int(amount) * UNITS[unit]
    return total
''',
        regression='''"""Parse durations such as '1h30m' into seconds."""

import re

UNITS = {"s": 60, "m": 60, "h": 3600}


def parse_duration(text: str) -> int:
    total = 0
    for amount, unit in re.findall(r"(\\d+)([smh])", text):
        total += int(amount) * UNITS[unit]
    return total
''',
        base_tests="""from timekit_duration import parse_duration


def test_seconds():
    assert parse_duration("45s") == 45


def test_hours():
    assert parse_duration("2h") == 7200


def test_empty_is_zero():
    assert parse_duration("") == 0
""",
        new_tests="""

def test_minutes():
    assert parse_duration("5m") == 300


def test_hours_and_minutes():
    assert parse_duration("1h30m") == 5400
""",
    ),
    Spec(
        slug="lru-1",
        package="cachekit_lru",
        issue="LRUCache.get() does not mark the key as recently used, so a key that was just "
        "read is evicted first.",
        base='''"""A small least-recently-used cache."""

from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._data = OrderedDict()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def put(self, key, value):
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)

    def __len__(self):
        return len(self._data)
''',
        fixed='''"""A small least-recently-used cache."""

from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._data = OrderedDict()

    def get(self, key, default=None):
        if key not in self._data:
            return default
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key, value):
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)

    def __len__(self):
        return len(self._data)
''',
        regression='''"""A small least-recently-used cache."""

from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._data = OrderedDict()

    def get(self, key, default=None):
        if key not in self._data:
            return default
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key, value):
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)

    def __len__(self):
        return self.capacity
''',
        base_tests="""from cachekit_lru import LRUCache


def test_put_and_get():
    cache = LRUCache(2)
    cache.put("a", 1)
    assert cache.get("a") == 1


def test_evicts_oldest():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.get("a") is None


def test_len_counts_entries():
    cache = LRUCache(5)
    cache.put("a", 1)
    cache.put("b", 2)
    assert len(cache) == 2
""",
        new_tests="""

def test_get_refreshes_recency():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    assert cache.get("a") == 1
    assert cache.get("b") is None
""",
    ),
    Spec(
        slug="csvrow-1",
        package="datakit_csv",
        issue="to_csv_row() does not quote fields: ['a,b', 'c'] gives 'a,b,c' (three columns), "
        "and embedded double quotes are not escaped.",
        base='''"""Format one CSV row."""


def to_csv_row(fields) -> str:
    return ",".join(str(f) for f in fields)
''',
        fixed='''"""Format one CSV row."""


def _quote(value) -> str:
    text = str(value)
    if any(ch in text for ch in ',"\\n'):
        text = '"' + text.replace('"', '""') + '"'
    return text


def to_csv_row(fields) -> str:
    return ",".join(_quote(f) for f in fields)
''',
        regression='''"""Format one CSV row."""


def _quote(value) -> str:
    text = str(value).strip()
    if any(ch in text for ch in ',"\\n'):
        text = '"' + text.replace('"', '""') + '"'
    return text


def to_csv_row(fields) -> str:
    return ",".join(_quote(f) for f in fields)
''',
        partial='''"""Format one CSV row."""


def _quote(value) -> str:
    text = str(value)
    if "," in text:
        text = '"' + text + '"'
    return text


def to_csv_row(fields) -> str:
    return ",".join(_quote(f) for f in fields)
''',
        base_tests="""from datakit_csv import to_csv_row


def test_plain_fields():
    assert to_csv_row(["a", "b", 1]) == "a,b,1"


def test_empty_row():
    assert to_csv_row([]) == ""


def test_whitespace_is_preserved():
    assert to_csv_row(["a ", " b"]) == "a , b"
""",
        new_tests='''

def test_comma_is_quoted():
    assert to_csv_row(["a,b", "c"]) == '"a,b",c'


def test_quote_is_escaped():
    assert to_csv_row(['say "hi"']) == '"say ""hi"""'
''',
    ),
]


def diff(path: str, old: str, new: str) -> str:
    """Unified diff for one existing file, with git-style a/ and b/ prefixes."""
    lines = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
    )
    return "".join(lines)


def build(spec: Spec) -> None:
    task_id = f"patchbench__{spec.slug}"
    task_dir = ROOT / task_id
    if task_dir.exists():
        shutil.rmtree(task_dir)
    src_path = f"{spec.package}/__init__.py"
    test_path = f"tests/test_{spec.package}.py"
    repo = task_dir / "repo"
    (repo / spec.package).mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / src_path).write_text(spec.base, encoding="utf-8")
    (repo / test_path).write_text(spec.base_tests, encoding="utf-8")

    gold = diff(src_path, spec.base, spec.fixed)
    test_patch = diff(test_path, spec.base_tests, spec.base_tests + spec.new_tests)
    hang_src = "while True:\n    pass\n" + spec.base

    subs = {
        "gold": (gold, "resolved"),
        "empty": ("", "unresolved"),
        "noop": (diff(src_path, spec.base, spec.base + "\n# TODO: fix this\n"), "unresolved"),
        "malformed": (
            f"--- a/{src_path}\n+++ b/{src_path}\n@@ -1,3 +1,3 @@\n"
            " this context does not exist\n-nor does this line\n+replacement\n",
            "apply_failed",
        ),
        "traversal": (
            "--- /dev/null\n+++ b/../escaped.txt\n@@ -0,0 +1 @@\n+written outside the repo\n",
            "apply_failed",
        ),
        "hang": (diff(src_path, spec.base, hang_src), "timeout"),
        "regression": (diff(src_path, spec.base, spec.regression), "unresolved"),
    }
    if spec.partial is not None:
        subs["partial"] = (diff(src_path, spec.base, spec.partial), "partial")

    task = Task(
        instance_id=task_id,
        repo=f"patchbench-fixtures/{spec.package}",
        base_commit="fixture-base",
        problem_statement=spec.issue,
        patch=gold,
        test_patch=test_patch,
        snapshot_path=repo,
    )
    executor = LocalExecutor()
    _, at_base = execute(task, "", executor, timeout=60)
    _, at_gold = execute(task, gold, executor, timeout=60)
    f2p = sorted(
        t
        for t, s in at_gold.statuses.items()
        if s == "PASSED" and at_base.statuses.get(t) != "PASSED"
    )
    p2p = sorted(
        t
        for t, s in at_gold.statuses.items()
        if s == "PASSED" and at_base.statuses.get(t) == "PASSED"
    )
    if not f2p:
        raise SystemExit(f"{task_id}: gold patch fixes no failing test")
    task.fail_to_pass, task.pass_to_pass = f2p, p2p

    (task_dir / "task.json").write_text(
        json.dumps(task.model_dump(by_alias=True), indent=2) + "\n", encoding="utf-8"
    )
    sub_dir = task_dir / "submissions"
    sub_dir.mkdir()
    for label, (patch, _) in subs.items():
        (sub_dir / f"{label}.patch").write_text(patch, encoding="utf-8")
    expected = {label: verdict for label, (_, verdict) in sorted(subs.items())}
    (sub_dir / "expected.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    print(f"{task_id}: F2P={len(f2p)} P2P={len(p2p)} submissions={len(subs)}")


if __name__ == "__main__":
    for item in SPECS:
        build(item)
