import org.jetbrains.kotlin.gradle.ExperimentalWasmDsl

plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.composeMultiplatform)
    alias(libs.plugins.composeCompiler)
    alias(libs.plugins.ktlint)
    alias(libs.plugins.detekt)
}

kotlin {
    js {
        browser()
        binaries.executable()
    }

    @OptIn(ExperimentalWasmDsl::class)
    wasmJs {
        browser()
        binaries.executable()
    }

    sourceSets {
        commonMain.dependencies {
            implementation(project(":shared"))

            implementation(libs.compose.ui)
        }
    }
}

detekt {
    // See shared/build.gradle.kts for why this is needed in Kotlin Multiplatform modules.
    source.setFrom(
        provider {
            kotlin.sourceSets
                .flatMap { it.kotlin.srcDirs }
                .filterNot { it.path.contains("${File.separator}generated${File.separator}") }
        },
    )
}
