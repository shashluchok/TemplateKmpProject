import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bootstrap_project import (
    PACKAGE_REFERENCE_FILES,
    SOURCE_ROOTS,
    TEMPLATE_APP_NAME,
    TEMPLATE_PACKAGE,
    BootstrapError,
    app_name_files,
    bootstrap,
    check_manifest_files_exist,
    check_not_default,
    check_package_dirs_available,
    check_target_root_available,
    check_template_state,
    load_config,
    package_to_path,
    rename_package_dirs,
    rename_project_root,
    replace_app_name_references,
    replace_in_file,
    replace_package_references,
    run_gradle_sync,
    validate_app_name,
    validate_package,
)


class LoadConfigTests(unittest.TestCase):
    def test_reads_app_name_and_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            toml_path = Path(tmp) / "template.toml"
            toml_path.write_text(
                'app_name = "TestApp"\npackage = "com.example.testapp"\n', encoding="utf-8"
            )
            self.assertEqual(load_config(toml_path), ("TestApp", "com.example.testapp"))

    def test_missing_file_raises(self):
        with self.assertRaises(BootstrapError):
            load_config(Path("/nonexistent/template.toml"))

    def test_missing_key_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            toml_path = Path(tmp) / "template.toml"
            toml_path.write_text('app_name = "TestApp"\n', encoding="utf-8")
            with self.assertRaises(BootstrapError):
                load_config(toml_path)


class PackageToPathTests(unittest.TestCase):
    def test_converts_dotted_package_to_path(self):
        self.assertEqual(package_to_path("com.example.app"), Path("com/example/app"))

    def test_single_segment_package(self):
        self.assertEqual(package_to_path("app"), Path("app"))


class ValidatePackageTests(unittest.TestCase):
    def test_accepts_multi_segment_package(self):
        validate_package("com.example.myapp")  # must not raise

    def test_accepts_single_segment_package(self):
        validate_package("myapp")  # must not raise

    def test_accepts_package_with_digits(self):
        validate_package("com.example2.myapp2")  # must not raise

    def test_rejects_uppercase(self):
        with self.assertRaises(BootstrapError):
            validate_package("com.Example.myapp")

    def test_rejects_segment_starting_with_digit(self):
        with self.assertRaises(BootstrapError):
            validate_package("com.2example.myapp")

    def test_rejects_hyphen(self):
        with self.assertRaises(BootstrapError):
            validate_package("com.my-example.app")

    def test_rejects_empty(self):
        with self.assertRaises(BootstrapError):
            validate_package("")

    def test_rejects_leading_dot(self):
        with self.assertRaises(BootstrapError):
            validate_package(".com.example")

    def test_rejects_trailing_dot(self):
        with self.assertRaises(BootstrapError):
            validate_package("com.example.")

    def test_rejects_consecutive_dots(self):
        with self.assertRaises(BootstrapError):
            validate_package("com..example")


class ValidateAppNameTests(unittest.TestCase):
    def test_accepts_plain_name(self):
        validate_app_name("TestApp")  # must not raise

    def test_rejects_empty(self):
        with self.assertRaises(BootstrapError):
            validate_app_name("")

    def test_rejects_space(self):
        # A space here would end up inside PRODUCT_BUNDLE_IDENTIFIER, which iOS
        # requires to be alphanumeric/hyphen/period only.
        with self.assertRaises(BootstrapError):
            validate_app_name("Test App")

    def test_rejects_leading_digit(self):
        with self.assertRaises(BootstrapError):
            validate_app_name("2TestApp")

    def test_rejects_punctuation(self):
        with self.assertRaises(BootstrapError):
            validate_app_name('Test"App')


class CheckNotDefaultTests(unittest.TestCase):
    def test_raises_when_both_still_default(self):
        with self.assertRaises(BootstrapError):
            check_not_default(TEMPLATE_APP_NAME, TEMPLATE_PACKAGE)

    def test_passes_when_either_changed(self):
        check_not_default("TestApp", TEMPLATE_PACKAGE)  # must not raise
        check_not_default(TEMPLATE_APP_NAME, "com.example.testapp")  # must not raise


class ReplaceInFileTests(unittest.TestCase):
    def test_replaces_all_occurrences_and_returns_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("foo bar foo baz foo", encoding="utf-8")
            count = replace_in_file(path, "foo", "qux")
            self.assertEqual(count, 3)
            self.assertEqual(path.read_text(encoding="utf-8"), "qux bar qux baz qux")

    def test_no_match_returns_zero_and_leaves_file_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("hello world", encoding="utf-8")
            count = replace_in_file(path, "foo", "qux")
            self.assertEqual(count, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), "hello world")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CheckTemplateStateTests(unittest.TestCase):
    def test_passes_on_pristine_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "App.kt",
                f"package {TEMPLATE_PACKAGE}\n",
            )
            _write(
                repo_root / "settings.gradle.kts",
                f'rootProject.name = "{TEMPLATE_APP_NAME}"\n',
            )
            check_template_state(repo_root, "com.example.testapp", "TestApp")  # must not raise

    def test_passes_on_already_bootstrapped_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path("com.example.testapp")
                / "App.kt",
                "package com.example.testapp\n",
            )
            _write(
                repo_root / "settings.gradle.kts",
                'rootProject.name = "TestApp"\n',
            )
            check_template_state(repo_root, "com.example.testapp", "TestApp")  # must not raise

    def test_raises_when_neither_pristine_nor_bootstrapped(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root / "settings.gradle.kts",
                'rootProject.name = "SomethingElse"\n',
            )
            with self.assertRaises(BootstrapError):
                check_template_state(repo_root, "com.example.testapp", "TestApp")

    def test_raises_when_marker_dir_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root / "settings.gradle.kts",
                f'rootProject.name = "{TEMPLATE_APP_NAME}"\n',
            )
            with self.assertRaises(BootstrapError):
                check_template_state(repo_root, "com.example.testapp", "TestApp")


def _write_all_manifest_files(repo_root: Path) -> None:
    for rel_path in PACKAGE_REFERENCE_FILES:
        _write(repo_root / rel_path, "placeholder\n")
    for rel_path in app_name_files(TEMPLATE_PACKAGE):
        _write(repo_root / rel_path, "placeholder\n")


class CheckManifestFilesExistTests(unittest.TestCase):
    def test_passes_when_all_manifest_files_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_all_manifest_files(repo_root)
            check_manifest_files_exist(repo_root, "com.example.testapp")  # must not raise

    def test_passes_when_files_are_at_bootstrapped_locations(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            for rel_path in PACKAGE_REFERENCE_FILES:
                _write(repo_root / rel_path, "placeholder\n")
            for rel_path in app_name_files("com.example.testapp"):
                _write(repo_root / rel_path, "placeholder\n")
            check_manifest_files_exist(repo_root, "com.example.testapp")  # must not raise

    def test_raises_listing_every_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_all_manifest_files(repo_root)
            (repo_root / "iosApp/Configuration/Config.xcconfig").unlink()
            with self.assertRaises(BootstrapError) as ctx:
                check_manifest_files_exist(repo_root, "com.example.testapp")
            self.assertIn("iosApp/Configuration/Config.xcconfig", str(ctx.exception))


class CheckPackageDirsAvailableTests(unittest.TestCase):
    def test_passes_when_nothing_at_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "App.kt",
                f"package {TEMPLATE_PACKAGE}\n",
            )
            check_package_dirs_available(repo_root, "com.example.testapp")  # must not raise

    def test_raises_when_target_package_dir_already_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "App.kt",
                f"package {TEMPLATE_PACKAGE}\n",
            )
            _write(
                repo_root / "androidApp/src/main/kotlin/com/example/testapp/Existing.kt",
                "package com.example.testapp\n",
            )
            with self.assertRaises(BootstrapError):
                check_package_dirs_available(repo_root, "com.example.testapp")

    def test_passes_when_target_is_an_empty_leftover_directory(self):
        # e.g. a previous bootstrap run got reverted (tracked template files
        # restored) but the untracked, now-empty target directories it had
        # created were left behind -- git never reports empty directories, so
        # this is easy to miss. Empty of real files anywhere inside (even
        # nested empty subdirectories, like an empty leftover "di") isn't a
        # conflict.
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "App.kt",
                f"package {TEMPLATE_PACKAGE}\n",
            )
            (
                repo_root / "androidApp/src/main/kotlin/com/example/testapp/di"
            ).mkdir(parents=True)
            check_package_dirs_available(repo_root, "com.example.testapp")  # must not raise


class RenamePackageDirsTests(unittest.TestCase):
    def test_renames_existing_roots_and_skips_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "App.kt",
                f"package {TEMPLATE_PACKAGE}\n",
            )
            _write(
                repo_root
                / "shared/src/commonMain/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "Foo.kt",
                f"package {TEMPLATE_PACKAGE}\n",
            )
            renamed = rename_package_dirs(repo_root, TEMPLATE_PACKAGE, "com.shashluchok.testapp")

            self.assertEqual(len(renamed), 2)
            self.assertTrue(
                (repo_root / "androidApp/src/main/kotlin/com/shashluchok/testapp").is_dir()
            )
            self.assertTrue(
                (repo_root / "shared/src/commonMain/kotlin/com/shashluchok/testapp").is_dir()
            )
            self.assertFalse(
                (
                    repo_root / "androidApp/src/main/kotlin" / package_to_path(TEMPLATE_PACKAGE)
                ).exists()
            )

    def test_shared_prefix_keeps_shared_ancestor_directories(self):
        # old and new package share "com/shashluchok" -- that ancestor must survive
        # since the renamed leaf now lives right next to where the old one was.
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "App.kt",
                f"package {TEMPLATE_PACKAGE}\n",
            )
            rename_package_dirs(repo_root, TEMPLATE_PACKAGE, "com.shashluchok.testapp")
            self.assertTrue((repo_root / "androidApp/src/main/kotlin/com/shashluchok").is_dir())
            self.assertTrue(
                (repo_root / "androidApp/src/main/kotlin/com/shashluchok/testapp").is_dir()
            )

    def test_clears_empty_leftover_target_before_moving_in(self):
        # Windows' Path.rename refuses to move onto an existing directory even
        # when it's empty -- the leftover (with a nested empty "di" subdirectory,
        # like an IDE-reverted rename can leave behind) must be cleared first, and
        # the real content still ends up there.
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "App.kt",
                f"package {TEMPLATE_PACKAGE}\n",
            )
            (
                repo_root / "androidApp/src/main/kotlin/com/example/testapp/di"
            ).mkdir(parents=True)

            renamed = rename_package_dirs(repo_root, TEMPLATE_PACKAGE, "com.example.testapp")

            self.assertEqual(len(renamed), 1)
            self.assertTrue(
                (
                    repo_root / "androidApp/src/main/kotlin/com/example/testapp/App.kt"
                ).is_file()
            )
            self.assertFalse(
                (repo_root / "androidApp/src/main/kotlin/com/example/testapp/di").exists()
            )

    def test_different_prefix_prunes_now_empty_old_ancestors(self):
        # old and new package share no segments -- "com/shashluchok" must be pruned
        # away entirely once it's empty, and "com" too if it becomes empty as a result.
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "App.kt",
                f"package {TEMPLATE_PACKAGE}\n",
            )
            rename_package_dirs(repo_root, TEMPLATE_PACKAGE, "org.example.testapp")
            self.assertFalse((repo_root / "androidApp/src/main/kotlin/com").exists())
            self.assertTrue(
                (repo_root / "androidApp/src/main/kotlin/org/example/testapp").is_dir()
            )
            self.assertTrue(
                (
                    repo_root / "androidApp/src/main/kotlin/org/example/testapp/App.kt"
                ).is_file()
            )

    def test_different_depth_package_still_renames_correctly(self):
        # new package has fewer segments than old -- directory nesting shrinks.
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "App.kt",
                f"package {TEMPLATE_PACKAGE}\n",
            )
            rename_package_dirs(repo_root, TEMPLATE_PACKAGE, "myapp")
            self.assertFalse((repo_root / "androidApp/src/main/kotlin/com").exists())
            self.assertTrue((repo_root / "androidApp/src/main/kotlin/myapp/App.kt").is_file())


class ReplacePackageReferencesTests(unittest.TestCase):
    def test_replaces_in_kt_files_under_renamed_dirs_and_in_fixed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            android_kt = (
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "App.kt"
            )
            _write(android_kt, f"package {TEMPLATE_PACKAGE}\n")
            _write(
                repo_root / "androidApp/build.gradle.kts",
                f'namespace = "{TEMPLATE_PACKAGE}"\n' f'applicationId = "{TEMPLATE_PACKAGE}"\n',
            )
            _write(
                repo_root / "shared/build.gradle.kts",
                f'namespace = "{TEMPLATE_PACKAGE}.shared"\n',
            )
            _write(
                repo_root / "desktopApp/build.gradle.kts",
                f'packageName = "{TEMPLATE_PACKAGE}"\n' f'mainClass = "{TEMPLATE_PACKAGE}.MainKt"\n',
            )
            _write(
                repo_root / "iosApp/Configuration/Config.xcconfig",
                "PRODUCT_BUNDLE_IDENTIFIER=" f"{TEMPLATE_PACKAGE}.{TEMPLATE_APP_NAME}\n",
            )

            renamed = rename_package_dirs(repo_root, TEMPLATE_PACKAGE, "com.shashluchok.testapp")
            counts = replace_package_references(
                repo_root,
                renamed,
                TEMPLATE_PACKAGE,
                "com.shashluchok.testapp",
            )

            new_kt = (
                repo_root / "androidApp/src/main/kotlin/com/shashluchok/testapp/App.kt"
            )
            self.assertEqual(new_kt.read_text(encoding="utf-8"), "package com.shashluchok.testapp\n")
            self.assertIn("androidApp/build.gradle.kts", counts)
            self.assertEqual(counts["androidApp/build.gradle.kts"], 2)
            self.assertEqual(
                (repo_root / "iosApp/Configuration/Config.xcconfig").read_text(encoding="utf-8"),
                "PRODUCT_BUNDLE_IDENTIFIER=" f"com.shashluchok.testapp.{TEMPLATE_APP_NAME}\n",
            )

    def test_replaces_with_a_completely_different_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root
                / "androidApp/src/main/kotlin"
                / package_to_path(TEMPLATE_PACKAGE)
                / "App.kt",
                f"package {TEMPLATE_PACKAGE}\n",
            )
            _write(
                repo_root / "androidApp/build.gradle.kts",
                f'namespace = "{TEMPLATE_PACKAGE}"\n',
            )
            _write(repo_root / "shared/build.gradle.kts", "\n")
            _write(repo_root / "desktopApp/build.gradle.kts", "\n")
            _write(repo_root / "iosApp/Configuration/Config.xcconfig", "\n")

            renamed = rename_package_dirs(repo_root, TEMPLATE_PACKAGE, "org.example.testapp")
            counts = replace_package_references(
                repo_root, renamed, TEMPLATE_PACKAGE, "org.example.testapp"
            )

            new_kt = repo_root / "androidApp/src/main/kotlin/org/example/testapp/App.kt"
            self.assertEqual(new_kt.read_text(encoding="utf-8"), "package org.example.testapp\n")
            self.assertEqual(
                (repo_root / "androidApp/build.gradle.kts").read_text(encoding="utf-8"),
                'namespace = "org.example.testapp"\n',
            )
            self.assertEqual(counts["androidApp/build.gradle.kts"], 1)


class AppNameFilesTests(unittest.TestCase):
    def test_desktop_main_kt_uses_new_package_path(self):
        files = app_name_files("com.example.testapp")
        self.assertIn(
            "desktopApp/src/main/kotlin/com/example/testapp/Main.kt", files
        )

    def test_desktop_main_kt_with_single_segment_package(self):
        files = app_name_files("myapp")
        self.assertIn("desktopApp/src/main/kotlin/myapp/Main.kt", files)


class ReplaceAppNameReferencesTests(unittest.TestCase):
    def test_replaces_in_every_known_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            for rel_path in app_name_files("com.example.testapp"):
                _write(repo_root / rel_path, f"{TEMPLATE_APP_NAME} placeholder\n")

            counts = replace_app_name_references(
                repo_root, "com.example.testapp", TEMPLATE_APP_NAME, "TestApp"
            )

            self.assertEqual(len(counts), len(app_name_files("com.example.testapp")))
            for rel_path in app_name_files("com.example.testapp"):
                self.assertEqual(
                    (repo_root / rel_path).read_text(encoding="utf-8"),
                    "TestApp placeholder\n",
                )


class CheckTargetRootAvailableTests(unittest.TestCase):
    def test_passes_when_nothing_at_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "old_name"
            repo_root.mkdir()
            check_target_root_available(repo_root, "NewName")  # must not raise

    def test_raises_when_target_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "old_name"
            repo_root.mkdir()
            (Path(tmp) / "NewName").mkdir()
            with self.assertRaises(BootstrapError):
                check_target_root_available(repo_root, "NewName")

    def test_passes_when_repo_already_named_target(self):
        # Already bootstrapped (or the folder happened to be named this way from the
        # start, e.g. by Android Studio) -- nothing to rename, not a conflict.
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "NewName"
            repo_root.mkdir()
            check_target_root_available(repo_root, "NewName")  # must not raise


class RenameProjectRootTests(unittest.TestCase):
    def test_renames_directory_and_returns_new_path(self):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            old_root = Path(tmp) / "old_name"
            _write(old_root / "settings.gradle.kts", 'rootProject.name = "Old"\n')

            new_root = rename_project_root(old_root, "NewName")
            try:
                self.assertEqual(new_root, Path(tmp) / "NewName")
                self.assertTrue(new_root.is_dir())
                self.assertFalse(old_root.exists())
                self.assertEqual(
                    (new_root / "settings.gradle.kts").read_text(encoding="utf-8"),
                    'rootProject.name = "Old"\n',
                )
            finally:
                os.chdir(original_cwd)

    def test_returns_unchanged_when_already_named_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "NewName"
            repo_root.mkdir()
            _write(repo_root / "marker.txt", "x")

            result = rename_project_root(repo_root, "NewName")

            self.assertEqual(result, repo_root)
            self.assertTrue(repo_root.is_dir())
            self.assertEqual((repo_root / "marker.txt").read_text(encoding="utf-8"), "x")


class RunGradleSyncTests(unittest.TestCase):
    @staticmethod
    def _wrapper_name() -> str:
        return "gradlew.bat" if os.name == "nt" else "gradlew"

    def test_skips_when_no_wrapper_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            with patch("bootstrap_project.subprocess.run") as mock_run:
                run_gradle_sync(repo_root)  # must not raise
            mock_run.assert_not_called()

    def test_runs_wrapper_and_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            wrapper = repo_root / self._wrapper_name()
            _write(wrapper, "echo sync\n")
            with patch("bootstrap_project.subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
                run_gradle_sync(repo_root)  # must not raise

            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            self.assertEqual(args[0], [str(wrapper), "tasks"])
            self.assertEqual(kwargs["cwd"], repo_root)

    def test_reports_failure_without_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(repo_root / self._wrapper_name(), "echo sync\n")
            with patch("bootstrap_project.subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1)
                run_gradle_sync(repo_root)  # must not raise


def _write_pristine_fixture(repo_root: Path) -> None:
    """Write a minimal but complete pristine-template fixture under `repo_root`
    -- one file per bootstrap manifest entry, so `bootstrap()` can run end to end."""
    _write(
        repo_root / "template.toml",
        'app_name = "TestApp"\npackage = "org.example.testapp"\n',
    )
    _write(
        repo_root / "androidApp/src/main/kotlin" / package_to_path(TEMPLATE_PACKAGE) / "App.kt",
        f"package {TEMPLATE_PACKAGE}\n",
    )
    _write(
        repo_root / "androidApp/build.gradle.kts",
        f'namespace = "{TEMPLATE_PACKAGE}"\n',
    )
    _write(repo_root / "shared/build.gradle.kts", f'namespace = "{TEMPLATE_PACKAGE}.shared"\n')
    _write(repo_root / "desktopApp/build.gradle.kts", f'packageName = "{TEMPLATE_PACKAGE}"\n')
    _write(
        repo_root / "desktopApp/src/main/kotlin" / package_to_path(TEMPLATE_PACKAGE) / "Main.kt",
        f'title = "{TEMPLATE_APP_NAME}",\n',
    )
    _write(
        repo_root / "androidApp/src/main/res/values/strings.xml",
        f'<string name="app_name">{TEMPLATE_APP_NAME}</string>\n',
    )
    _write(
        repo_root / "webApp/src/webMain/resources/index.html",
        f"<title>{TEMPLATE_APP_NAME}</title>\n",
    )
    _write(
        repo_root / "settings.gradle.kts",
        f'rootProject.name = "{TEMPLATE_APP_NAME}"\n',
    )
    _write(
        repo_root / "iosApp/Configuration/Config.xcconfig",
        f"PRODUCT_NAME={TEMPLATE_APP_NAME}\n"
        "PRODUCT_BUNDLE_IDENTIFIER="
        f"{TEMPLATE_PACKAGE}.{TEMPLATE_APP_NAME}\n",
    )
    _write(
        repo_root / "iosApp/iosApp.xcodeproj/project.pbxproj",
        f"path = {TEMPLATE_APP_NAME}.app;\n",
    )


class BootstrapEndToEndTests(unittest.TestCase):
    def test_full_run_renames_and_replaces_everything(self):
        # bootstrap() renames repo_root itself as its last step, so it can't live
        # inside a tempfile.TemporaryDirectory() (which would try to delete the
        # original, now-gone path on exit) -- manage the temp dir by hand instead.
        original_cwd = os.getcwd()
        tmp_parent = Path(tempfile.mkdtemp())
        repo_root = tmp_parent / "old_name"
        repo_root.mkdir()
        try:
            _write_pristine_fixture(repo_root)

            with patch("bootstrap_project.run_gradle_sync") as mock_sync:
                new_root = bootstrap(repo_root, repo_root / "template.toml")  # must not raise

            # real changes happened -- gradle sync must run, against the final
            # (renamed) location.
            mock_sync.assert_called_once_with(new_root)
            self.assertEqual(new_root, tmp_parent / "TestApp")
            self.assertFalse(repo_root.exists())
            # package went from TEMPLATE_PACKAGE (sharing no prefix with the new one)
            # to org.example.testapp -- proves the rename isn't limited to swapping
            # the last path segment.
            self.assertEqual(
                (
                    new_root / "androidApp/src/main/kotlin/org/example/testapp/App.kt"
                ).read_text(encoding="utf-8"),
                "package org.example.testapp\n",
            )
            self.assertFalse((new_root / "androidApp/src/main/kotlin/com").exists())
            self.assertEqual(
                (new_root / "settings.gradle.kts").read_text(encoding="utf-8"),
                'rootProject.name = "TestApp"\n',
            )
            self.assertEqual(
                (new_root / "iosApp/Configuration/Config.xcconfig").read_text(encoding="utf-8"),
                "PRODUCT_NAME=TestApp\n"
                "PRODUCT_BUNDLE_IDENTIFIER=org.example.testapp.TestApp\n",
            )
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(tmp_parent, ignore_errors=True)

    def test_folder_rename_failure_keeps_completed_work_and_returns_original_root(self):
        # On Windows, renaming the project folder itself can fail with a WinError 32
        # ("file in use") if the invoking shell's own cwd is inside it -- this is common
        # (e.g. `cd my-project && python bootstrap/bootstrap_project.py`), not a bug in the
        # script. bootstrap() must not treat that as a reason to unwind everything else
        # that already succeeded.
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_pristine_fixture(repo_root)

            with patch(
                "bootstrap_project.rename_project_root",
                side_effect=OSError("[WinError 32] file in use"),
            ), patch("bootstrap_project.run_gradle_sync") as mock_sync:
                result = bootstrap(repo_root, repo_root / "template.toml")  # must not raise

            # package/name changes succeeded despite the folder rename failing --
            # gradle sync must still run, against the (unrenamed) original root.
            mock_sync.assert_called_once_with(repo_root)
            self.assertEqual(result, repo_root)
            self.assertTrue(repo_root.is_dir())
            self.assertEqual(
                (
                    repo_root / "androidApp/src/main/kotlin/org/example/testapp/App.kt"
                ).read_text(encoding="utf-8"),
                "package org.example.testapp\n",
            )
            self.assertEqual(
                (repo_root / "settings.gradle.kts").read_text(encoding="utf-8"),
                'rootProject.name = "TestApp"\n',
            )

    def test_second_run_after_success_is_idempotent(self):
        # Re-running bootstrap() against an already-bootstrapped repo (e.g. because
        # the project folder happened to already be named app_name, so the previous
        # run's last step was a no-op) must succeed as a no-op, not raise.
        original_cwd = os.getcwd()
        tmp_parent = Path(tempfile.mkdtemp())
        repo_root = tmp_parent / "old_name"
        repo_root.mkdir()
        try:
            _write_pristine_fixture(repo_root)
            new_root = bootstrap(repo_root, repo_root / "template.toml")
            self.assertEqual(new_root, tmp_parent / "TestApp")

            with patch("bootstrap_project.run_gradle_sync") as mock_sync:
                second_result = bootstrap(new_root, new_root / "template.toml")

            # nothing left to rename/replace on the second run -- gradle sync must
            # be skipped, not re-run against an already-synced project.
            mock_sync.assert_not_called()
            self.assertEqual(second_result, new_root)
            self.assertEqual(
                (
                    new_root / "androidApp/src/main/kotlin/org/example/testapp/App.kt"
                ).read_text(encoding="utf-8"),
                "package org.example.testapp\n",
            )
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(tmp_parent, ignore_errors=True)

    def test_second_run_without_editing_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write(
                repo_root / "template.toml",
                f'app_name = "{TEMPLATE_APP_NAME}"\npackage = "{TEMPLATE_PACKAGE}"\n',
            )
            with self.assertRaises(BootstrapError):
                bootstrap(repo_root, repo_root / "template.toml")


class ManifestDriftTests(unittest.TestCase):
    """Regression tests that run against the REAL repository this script lives in
    (not a tempdir fixture), guarding against SOURCE_ROOTS / PACKAGE_REFERENCE_FILES /
    app_name_files drifting out of sync with the actual repo structure -- the exact gap
    that let a broken README link and missing source roots slip through review."""

    REPO_ROOT = Path(__file__).resolve().parent.parent
    EXEMPT_DIR_PREFIXES = ("bootstrap/", "docs/")
    MARKERS = (TEMPLATE_APP_NAME, TEMPLATE_PACKAGE)

    def test_all_manifest_paths_exist_in_real_repo(self):
        manifest_paths = list(PACKAGE_REFERENCE_FILES) + app_name_files(TEMPLATE_PACKAGE)
        missing = [p for p in manifest_paths if not (self.REPO_ROOT / p).is_file()]
        self.assertEqual(missing, [], f"manifest paths missing from real repo: {missing}")

    def test_no_untracked_template_markers_outside_manifests(self):
        result = subprocess.run(
            ["git", "-C", str(self.REPO_ROOT), "ls-files"],
            capture_output=True,
            text=True,
            check=True,
        )
        tracked_files = [line for line in result.stdout.splitlines() if line]

        manifest_covered = set(PACKAGE_REFERENCE_FILES) | set(
            app_name_files(TEMPLATE_PACKAGE)
        )

        offenders = []
        for rel_path in tracked_files:
            if rel_path.startswith(self.EXEMPT_DIR_PREFIXES):
                continue
            if rel_path in manifest_covered:
                continue
            if any(rel_path.startswith(f"{root}/") for root in SOURCE_ROOTS):
                continue

            file_path = self.REPO_ROOT / rel_path
            if not file_path.is_file():
                continue  # e.g. a submodule gitlink or broken symlink entry
            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue  # binary/unreadable -- can't meaningfully contain the marker

            if any(marker in text for marker in self.MARKERS):
                offenders.append(rel_path)

        self.assertEqual(
            offenders,
            [],
            "tracked files outside bootstrap/ and docs/ contain a template "
            f"identity marker but aren't covered by any manifest: {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
