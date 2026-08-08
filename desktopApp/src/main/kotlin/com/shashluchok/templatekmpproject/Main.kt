package com.shashluchok.templatekmpproject

import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import com.shashluchok.templatekmpproject.presentation.navigation.AppContent

fun main() =
    application {
        Window(
            onCloseRequest = ::exitApplication,
            title = "TemplateKmpProject",
        ) {
            AppContent()
        }
    }
