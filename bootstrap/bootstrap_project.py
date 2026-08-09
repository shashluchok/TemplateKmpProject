#!/usr/bin/env python3
"""Bootstrap: renames this template's app identity (Kotlin package + display
name) to a new project's, based on template.toml.

Run on a pristine clone of the template, after editing template.toml (both
live in this same directory):
    python bootstrap/bootstrap_project.py

Safe to re-run: any marker (package dirs, name references, the project
folder itself) already at template.toml's values is left alone instead of
raising -- only a marker stuck in neither the template's nor the configured
state is treated as an error.

Once it succeeds, this whole `bootstrap/` directory is no longer needed --
delete it.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

TEMPLATE_PACKAGE = "com.shashluchok.templatekmpproject"
TEMPLATE_APP_NAME = "TemplateKmpProject"

PACKAGE_SEGMENT = r"[a-z][a-z0-9]*"
PACKAGE_RE = re.compile(rf"{PACKAGE_SEGMENT}(\.{PACKAGE_SEGMENT})*")
APP_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")


class BootstrapError(Exception):
    """Raised for any condition that should stop the bootstrap before it touches files."""


def package_to_path(package: str) -> Path:
    """Convert a dotted package name (`com.example.app`) to a relative directory
    path (`com/example/app`)."""
    return Path(*package.split("."))


def load_config(path: Path) -> tuple[str, str]:
    """Read template.toml. Returns (app_name, package)."""
    if not path.exists():
        raise BootstrapError(f"{path} not found")
    with path.open("rb") as f:
        data = tomllib.load(f)
    try:
        return data["app_name"], data["package"]
    except KeyError as e:
        raise BootstrapError(f"{path} is missing required key: {e}") from e


def validate_package(package: str) -> None:
    if not PACKAGE_RE.fullmatch(package):
        raise BootstrapError(
            f"package {package!r} must be one or more dot-separated lowercase "
            "letters/digits segments, each starting with a letter (a valid "
            "Kotlin/Java package, e.g. com.example.myapp) -- no leading/trailing/"
            "consecutive dots"
        )


def validate_app_name(name: str) -> None:
    if not APP_NAME_RE.fullmatch(name):
        raise BootstrapError(
            f"app_name {name!r} must be a single word of letters/digits, starting "
            "with a letter -- no spaces or punctuation. It's embedded verbatim into "
            "PRODUCT_BUNDLE_IDENTIFIER (iOS bundle ids can't contain spaces) as well "
            "as XML/xcconfig/HTML."
        )


def check_not_default(app_name: str, package: str) -> None:
    if app_name == TEMPLATE_APP_NAME and package == TEMPLATE_PACKAGE:
        raise BootstrapError(
            "template.toml still has the template's own values -- edit app_name and "
            "package before running this script"
        )


def replace_in_file(path: Path, old: str, new: str) -> int:
    """Replace all occurrences of `old` with `new` in `path`. Returns the count."""
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count:
        path.write_text(text.replace(old, new), encoding="utf-8")
    return count


SOURCE_ROOTS = [
    "androidApp/src/main/kotlin",
    "desktopApp/src/main/kotlin",
    "webApp/src/webMain/kotlin",
    "shared/src/commonMain/kotlin",
    "shared/src/commonTest/kotlin",
    "shared/src/androidMain/kotlin",
    "shared/src/androidHostTest/kotlin",
    "shared/src/iosMain/kotlin",
    "shared/src/iosTest/kotlin",
    "shared/src/jvmMain/kotlin",
    "shared/src/jvmTest/kotlin",
    "shared/src/jsMain/kotlin",
    "shared/src/wasmJsMain/kotlin",
    "shared/src/webTest/kotlin",
]

# Non-.kt files (relative to repo root) that reference the package outside SOURCE_ROOTS.
PACKAGE_REFERENCE_FILES = [
    "androidApp/build.gradle.kts",
    "shared/build.gradle.kts",
    "desktopApp/build.gradle.kts",
    "iosApp/Configuration/Config.xcconfig",
]


def check_template_state(repo_root: Path, package: str, app_name: str) -> None:
    """Verify the repo is either a pristine template checkout (still at the
    template's own package/app name -- about to be bootstrapped) or already
    bootstrapped to template.toml's current `package`/`app_name` (nothing left
    to do here -- every step below is a no-op for whatever's already in
    place). Anything else means the repo is in an unexpected, drifted state
    and bootstrapping should stop before touching anything."""
    template_marker = repo_root / "androidApp/src/main/kotlin" / package_to_path(TEMPLATE_PACKAGE)
    bootstrapped_marker = repo_root / "androidApp/src/main/kotlin" / package_to_path(package)
    settings_file = repo_root / "settings.gradle.kts"
    settings_text = settings_file.read_text(encoding="utf-8") if settings_file.exists() else ""

    package_ok = template_marker.is_dir() or bootstrapped_marker.is_dir()
    name_ok = TEMPLATE_APP_NAME in settings_text or app_name in settings_text
    if not package_ok or not name_ok:
        raise BootstrapError(
            "this doesn't look like a pristine template checkout, nor one already "
            f"bootstrapped to template.toml's values (expected {template_marker} or "
            f"{bootstrapped_marker} to exist, and either {TEMPLATE_APP_NAME!r} or "
            f"{app_name!r} in settings.gradle.kts) -- already bootstrapped to "
            "different values, or the template structure changed"
        )


def app_name_files(new_package: str) -> list[str]:
    """Repo-relative paths of files that embed the display name. desktopApp's
    Main.kt lives under the package directory, so it's built from `new_package`
    -- call this *after* the package rename."""
    package_path = "/".join(new_package.split("."))
    return [
        "androidApp/src/main/res/values/strings.xml",
        f"desktopApp/src/main/kotlin/{package_path}/Main.kt",
        "webApp/src/webMain/resources/index.html",
        "settings.gradle.kts",
        "iosApp/Configuration/Config.xcconfig",
        "iosApp/iosApp.xcodeproj/project.pbxproj",
    ]


def check_manifest_files_exist(repo_root: Path, package: str) -> None:
    """Verify every file this script is about to touch actually exists -- at its
    pristine-template location, or, for whatever's already bootstrapped, at its
    template.toml-configured location -- before any filesystem mutation happens.
    Catches manifest/repo drift early instead of leaving a half-renamed repo after
    a mid-run crash."""
    missing = []
    for rel_path in PACKAGE_REFERENCE_FILES:
        if not (repo_root / rel_path).is_file():
            missing.append(rel_path)
    for template_path, bootstrapped_path in zip(
        app_name_files(TEMPLATE_PACKAGE), app_name_files(package)
    ):
        if not (repo_root / template_path).is_file() and not (
            repo_root / bootstrapped_path
        ).is_file():
            missing.append(template_path)
    if missing:
        raise BootstrapError(
            "the following files listed in this script's manifests are missing -- "
            "the template structure has drifted out of sync with bootstrap_project.py:\n"
            + "\n".join(f"  {p}" for p in missing)
        )


def _has_no_files(path: Path) -> bool:
    """True if `path` contains no regular file anywhere within it -- only, at
    most, nested empty directories."""
    return not any(p.is_file() for p in path.rglob("*"))


def check_package_dirs_available(repo_root: Path, new_package: str) -> None:
    """Verify the new package's directory doesn't already exist -- with real
    content -- under any source root that's about to be renamed into it, before
    any mutation starts. A leftover directory at the target that's empty of
    real files (e.g. an empty scaffold left behind by a reverted previous run)
    isn't a conflict -- rename_package_dirs clears it out of the way instead of
    raising."""
    old_path = package_to_path(TEMPLATE_PACKAGE)
    new_path = package_to_path(new_package)
    conflicts = []
    for root in SOURCE_ROOTS:
        old_dir = repo_root / root / old_path
        new_dir = repo_root / root / new_path
        if not old_dir.is_dir() or new_dir == old_dir or not new_dir.exists():
            continue
        if new_dir.is_dir() and _has_no_files(new_dir):
            continue
        conflicts.append(str(new_dir.relative_to(repo_root)))
    if conflicts:
        raise BootstrapError(
            "cannot rename the package -- these paths already exist:\n"
            + "\n".join(f"  {p}" for p in conflicts)
        )


def check_target_root_available(repo_root: Path, new_name: str) -> None:
    """The project root directory itself gets renamed to `new_name` as the last
    bootstrap step -- verify nothing already occupies that path before any
    mutation starts. If the root is already named `new_name`, it's already
    bootstrapped -- nothing to rename, and no conflict to check."""
    if repo_root.name == new_name:
        return
    target = repo_root.parent / new_name
    if target.exists():
        raise BootstrapError(
            f"cannot rename project folder to {target} -- something already exists there"
        )


def _prune_empty_ancestors(start: Path, stop_before: Path) -> None:
    """Remove `start` and each now-empty parent directory, stopping at (and not
    removing) `stop_before`."""
    current = start
    while current != stop_before and current.is_dir() and not any(current.iterdir()):
        current.rmdir()
        current = current.parent


def rename_package_dirs(repo_root: Path, old_package: str, new_package: str) -> list[Path]:
    """Move the package directory (`.../com/old/pkg`) to its new nested path
    (`.../new/pkg`) under every SOURCE_ROOTS entry where it exists -- old and new
    can have different depth and share no segments at all. Prunes any now-empty
    old parent directories left behind. If the target already exists as an empty
    (of real files) leftover -- e.g. from a reverted previous run -- clears it
    first: `Path.rename` refuses to move onto an existing directory at all on
    Windows, even an empty one. Returns the list of new package paths."""
    old_path = package_to_path(old_package)
    new_path = package_to_path(new_package)
    renamed = []
    for root in SOURCE_ROOTS:
        root_dir = repo_root / root
        old_dir = root_dir / old_path
        if not old_dir.is_dir():
            continue
        new_dir = root_dir / new_path
        if new_dir.is_dir() and new_dir != old_dir and _has_no_files(new_dir):
            shutil.rmtree(new_dir)
        new_dir.parent.mkdir(parents=True, exist_ok=True)
        old_dir.rename(new_dir)
        _prune_empty_ancestors(old_dir.parent, root_dir)
        renamed.append(new_dir)
    return renamed


def replace_package_references(
    repo_root: Path, package_dirs: list[Path], old_package: str, new_package: str
) -> dict[str, int]:
    """Replace `old_package` with `new_package` in every .kt file under the
    renamed package dirs, plus PACKAGE_REFERENCE_FILES."""
    counts: dict[str, int] = {}

    files = []
    for package_dir in package_dirs:
        files.extend(sorted(package_dir.rglob("*.kt")))
    files.extend(repo_root / f for f in PACKAGE_REFERENCE_FILES)

    for file in files:
        n = replace_in_file(file, old_package, new_package)
        if n:
            counts[str(file.relative_to(repo_root).as_posix())] = n
    return counts


def replace_app_name_references(
    repo_root: Path, new_package: str, old_name: str, new_name: str
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rel_path in app_name_files(new_package):
        n = replace_in_file(repo_root / rel_path, old_name, new_name)
        if n:
            counts[rel_path] = n
    return counts


def rename_project_root(repo_root: Path, new_name: str) -> Path:
    """Rename the repo root directory itself to `new_name` (a sibling of its
    current parent). Must run last, after every other mutation, since the old
    `repo_root` path stops existing once this returns. Changes the process's
    cwd to the parent first -- on Windows, renaming a directory that's the
    current working directory of a running process fails with a permission
    error. If the root is already named `new_name`, there's nothing to
    rename."""
    if repo_root.name == new_name:
        return repo_root
    new_root = repo_root.parent / new_name
    os.chdir(repo_root.parent)
    repo_root.rename(new_root)
    return new_root


def run_gradle_sync(repo_root: Path) -> None:
    """Emulate an IDE "Gradle sync" from the CLI: `gradlew tasks` fully configures
    every module/target without building anything -- the cheapest way to catch a
    build script left broken by the renames above. Non-fatal: the renames already
    succeeded by the time this runs, so a sync failure is reported, not raised --
    the user can always re-sync from their IDE."""
    wrapper = repo_root / ("gradlew.bat" if os.name == "nt" else "gradlew")
    if not wrapper.is_file():
        print(f"\nSkipping gradle sync -- no wrapper found at {wrapper}")
        return

    print(f"\nRunning gradle sync ({wrapper.name} tasks)...")
    result = subprocess.run([str(wrapper), "tasks"], cwd=repo_root, shell=(os.name == "nt"))
    if result.returncode != 0:
        print(
            f"\ngradle sync failed (exit {result.returncode}) -- the rename itself "
            "succeeded above; inspect the Gradle output and re-sync from your IDE."
        )


def bootstrap(repo_root: Path, config_path: Path) -> Path:
    """Runs the full bootstrap. Safe to re-run -- any marker already at its
    template.toml-configured value is left alone instead of raising. Returns
    the project root's new path -- the directory itself gets renamed to
    `app_name` as the last step, so the original `repo_root` no longer exists
    once this returns (unless that last step failed or wasn't needed, in
    which case `repo_root` is returned unchanged -- see below). If anything
    was actually renamed/replaced, finishes with a gradle sync; a re-run that
    turns out to be a full no-op skips it."""
    app_name, package = load_config(config_path)
    validate_package(package)
    validate_app_name(app_name)
    check_not_default(app_name, package)
    check_template_state(repo_root, package, app_name)
    check_manifest_files_exist(repo_root, package)
    check_package_dirs_available(repo_root, package)
    check_target_root_available(repo_root, app_name)

    package_dirs = rename_package_dirs(repo_root, TEMPLATE_PACKAGE, package)
    package_counts = replace_package_references(repo_root, package_dirs, TEMPLATE_PACKAGE, package)
    name_counts = replace_app_name_references(repo_root, package, TEMPLATE_APP_NAME, app_name)

    print(f"Renamed {len(package_dirs)} package director{'y' if len(package_dirs) == 1 else 'ies'}:")
    for d in package_dirs:
        print(f"  {d.relative_to(repo_root)}")
    print(f"\nPackage reference replaced in {len(package_counts)} file(s):")
    for path, n in sorted(package_counts.items()):
        print(f"  {path} ({n})")
    print(f"\nDisplay name replaced in {len(name_counts)} file(s):")
    for path, n in sorted(name_counts.items()):
        print(f"  {path} ({n})")

    print(
        "\nThis only substitutes text -- it doesn't reorder Kotlin imports, so if the "
        "new package's alphabetical position differs a lot from the old one, ktlint may "
        "flag import order in a few files. Run `./gradlew ktlintFormat` once to auto-fix."
    )

    changed = bool(package_dirs) or bool(package_counts) or bool(name_counts)

    if repo_root.name == app_name:
        print(f"\nProject folder is already named '{app_name}' -- nothing to rename.")
        final_root = repo_root
    else:
        try:
            final_root = rename_project_root(repo_root, app_name)
        except OSError as e:
            print(
                f"\nEverything above succeeded -- only renaming the project folder itself "
                f"failed: {e}\n"
                "This usually means another process (this terminal, an IDE, a File Explorer "
                f"window) has {repo_root} open as its current directory. Close anything else "
                "pointed at this folder, then rename it yourself, e.g.:\n"
                f"  mv {repo_root} {repo_root.parent / app_name}"
            )
            final_root = repo_root
        else:
            print(f"\nProject folder renamed:\n  {repo_root}\n  -> {final_root}")
            print(
                f"\nYour shell is still in the old (now-deleted) directory -- run:\n"
                f"  cd {final_root}"
            )

    if changed:
        run_gradle_sync(final_root)

    return final_root


def main() -> int:
    import sys

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    config_path = script_dir / "template.toml"
    try:
        bootstrap(repo_root, config_path)
    except BootstrapError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        print(
            "the repository may be left in a partially-modified state -- to recover, "
            "discard all local changes with:\n  git checkout . && git clean -fd",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
