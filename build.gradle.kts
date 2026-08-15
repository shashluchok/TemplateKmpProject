import io.gitlab.arturbosch.detekt.Detekt
import io.gitlab.arturbosch.detekt.extensions.DetektExtension
import org.gradle.api.file.FileTree
import org.gradle.api.provider.Provider
import org.jlleitschuh.gradle.ktlint.KtlintExtension
import org.jlleitschuh.gradle.ktlint.tasks.KtLintCheckTask
import org.jlleitschuh.gradle.ktlint.tasks.KtLintFormatTask

plugins {
    // this is necessary to avoid the plugins to be loaded multiple times
    // in each subproject's classloader
    alias(libs.plugins.androidApplication) apply false
    alias(libs.plugins.androidMultiplatformLibrary) apply false
    alias(libs.plugins.composeMultiplatform) apply false
    alias(libs.plugins.composeCompiler) apply false
    alias(libs.plugins.kotlinJvm) apply false
    alias(libs.plugins.kotlinMultiplatform) apply false
    alias(libs.plugins.ktlint) apply false
    alias(libs.plugins.detekt) apply false
}

// Point Git at the repo-tracked hooks (.githooks/) so the pre-commit checks (string
// resource key format, ktlint, detekt) run for every contributor without a manual setup
// step. Cheap and idempotent -- safe to check/set on every configuration pass.
if (rootDir.resolve(".githooks").isDirectory) {
    val currentHooksPath = providers.exec {
        commandLine("git", "config", "--get", "core.hooksPath")
        isIgnoreExitValue = true
    }.standardOutput.asText.get().trim()
    if (currentHooksPath != ".githooks") {
        providers.exec {
            commandLine("git", "config", "core.hooksPath", ".githooks")
        }.result.get()
    }
}

// Files staged for commit (the git index), resolved against [rootDir]. Used to scope
// detekt to only what's actually about to be committed when run with -Pprecommit=true.
// See https://detekt.dev/docs/gettingstarted/git-pre-commit-hook/
fun Project.getGitStagedFiles(rootDir: File): Provider<List<File>> =
    providers.exec {
        commandLine("git", "--no-pager", "diff", "--name-only", "--cached")
    }.standardOutput.asText.map { output ->
        output.trim()
            .split("\n")
            .filter { it.isNotBlank() }
            .map { File(rootDir, it) }
    }

// Restricts [task]'s input to only the files staged for commit under this project (via
// [setSource], since ktlint's and detekt's task types don't share a common source-setting
// supertype), and disables UP-TO-DATE/build-cache reuse for it (the git index isn't a
// tracked Gradle input, so Gradle can't tell "staged files changed since the last commit"
// from "nothing changed" -- force a real re-run every time). Shared by ktlint and detekt
// below, both scoped to staged files when .githooks/pre-commit passes -Pprecommit=true,
// instead of the whole module (faster, matches what's committed).
fun Task.scopeToGitStagedFiles(project: Project, setSource: (Provider<FileTree>) -> Unit) {
    val rootDir = project.rootDir
    val projectDir = project.projectDir
    val stagedFileTree = project.files()
    setSource(
        project.getGitStagedFiles(rootDir).map { stagedFiles ->
            stagedFileTree.setFrom(*stagedFiles.filter { it.startsWith(projectDir) }.toTypedArray())
            stagedFileTree.asFileTree
        },
    )
    outputs.upToDateWhen { false }
    outputs.cacheIf { false }
}

subprojects {
    plugins.withId("org.jlleitschuh.gradle.ktlint") {
        dependencies {
            add("ktlintRuleset", libs.compose.rules)
        }
        extensions.configure<KtlintExtension> {
            // Compose Multiplatform resource accessors are generated into the source set
            // and must not be linted as if they were hand-written code.
            filter {
                exclude { entry -> entry.file.path.contains("${File.separator}generated${File.separator}") }
            }
        }
        tasks.withType<KtLintCheckTask>().configureEach {
            if (project.hasProperty("precommit")) {
                scopeToGitStagedFiles(project) { setSource(it) }
            }
        }
        tasks.withType<KtLintFormatTask>().configureEach {
            if (project.hasProperty("precommit")) {
                scopeToGitStagedFiles(project) { setSource(it) }
            }
        }
    }
    plugins.withId("io.gitlab.arturbosch.detekt") {
        dependencies {
            add("detektPlugins", libs.compose.rules.detekt)
        }
        extensions.configure<DetektExtension> {
            buildUponDefaultConfig = true
            parallel = true
            config.setFrom(files("$rootDir/config/detekt/detekt.yml"))
        }
        tasks.withType<Detekt>().configureEach {
            exclude("**/generated/**")
            if (project.hasProperty("precommit")) {
                scopeToGitStagedFiles(project) { setSource(it) }
            }
        }
    }
}
