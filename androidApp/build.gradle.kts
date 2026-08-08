import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    alias(libs.plugins.androidApplication)
    alias(libs.plugins.composeCompiler)
    alias(libs.plugins.ktlint)
    alias(libs.plugins.detekt)
}

kotlin {
    compilerOptions {
        jvmTarget = JvmTarget.JVM_11
    }
}
dependencies {
    implementation(project(":shared"))

    implementation(libs.androidx.activity.compose)
    implementation(libs.koin.core)
    implementation(libs.compose.uiToolingPreview)
    debugImplementation(libs.compose.uiTooling)
}

android {
    namespace = "com.shashluchok.templatekmpproject"
    // Plain `compileSdk = 37` resolves to the SDK Manager target "android-37", but the
    // installed platform for API 37 is "android-37.0" (Android's new major.minor SDK
    // release scheme -- see https://developer.android.com/build/releases/agp-9-0-0-release-notes).
    compileSdk {
        version =
            release(
                libs.versions.android.compileSdk
                    .get()
                    .toInt(),
            ) {
                minorApiLevel =
                    libs.versions.android.compileSdkMinor
                        .get()
                        .toInt()
            }
    }

    defaultConfig {
        applicationId = "com.shashluchok.templatekmpproject"
        minSdk =
            libs.versions.android.minSdk
                .get()
                .toInt()
        targetSdk =
            libs.versions.android.targetSdk
                .get()
                .toInt()
        versionCode = 1
        versionName = "1.0"
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        compose = true
    }
}
