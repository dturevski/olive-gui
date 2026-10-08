# yacpdb-common

The shared Python library lives in the public Olive repository and has its own
version in the root `pyproject.toml`. Only the `yacpdb` package is installed;
the desktop GUI, configuration/startup, Qt and exporters are excluded.

## Public interfaces

- `yacpdb.board`: board and piece model; packaged fairy-piece and font data.
- `yacpdb.model`: shared entry helpers, normalization and Popeye transformations.
- `yacpdb.entry`: YAML entry loading, conversion and transliteration.
- `yacpdb.validation`: `load_schema`, `validate`, `validateEntity` and CLI.
- `yacpdb.p2w`: solution lexer, parser and node traversal.
- `yacpdb.legacy`: existing Popeye input/output and chess helpers.
- `yacpdb.indexer`: query parser, predicates, documentation and analyzers.
- `yacpdb.storage`: existing MySQL execution/indexer adapter; connections are lazy.

Importing these modules does not change cwd or sys.path, configure logging,
load desktop settings, or require Qt. Data files are resolved relative to the
installed package. Parser construction writes no tables or debug output.
`PredicateStorage()` uses packaged documentation; its old optional checkout
argument remains compatible for callers that deliberately supply alternate docs.

`validate(entry, propagate_exceptions=False)` returns structured failures;
its default raises validation exceptions. Explicit validation uses the schema's
Draft 7 dialect. Olive local draft editing remains lenient and does not invoke
this strict validation implicitly.

```sh
python -m yacpdb.validation --validate request.json
python -m yacpdb.validation --validate person.json person
yacpdb-validate --validate request.json
python -m yacpdb.indexer.cruncher --crunch
```

The validator retains the existing JSON response format and conversion command.
Schemas and their format documentation remain in `yacpdb/schemas/`.
Olive's root `model.py` retains collection state and reexports shared helpers;
root `validate.py` is a compatibility launcher. Application startup and logging
remain in desktop `base.py`. `FairyHelper(config_dir=...)` permits explicit desktop
configuration overrides with packaged defaults; Olive initializes those at startup.

## Installation and checks

```sh
python -m pip install -e /path/to/olive-gui
python -m pip wheel --no-deps /path/to/olive-gui -w /path/to/wheels
```

Use a recent pip (21.3 or later) for editable pyproject installation. The package
supports Python 3.8 and later and declares its library dependencies independently
of desktop `requirements.txt`. Bump the library version for a released API/data
change; consuming applications install the tested wheel version. Repository
extraction is not required.

From the private sibling YACPDB checkout, run `python tools/check_common.py` with
an interpreter that has the packaging tools and dependencies installed. This
builds and installs a wheel and tests it outside both source trees, including wiki
consumers. `tests/unit/common_package.py` in Olive can also run against an installed
package with `python -I /path/to/olive-gui/tests/unit/common_package.py`.

Frozen desktop builds include `yacpdb` data in their specs and Windows build
command. The old py2exe-only setup script is named `setup_py2exe.py` so it cannot
interfere with modern library builds.
