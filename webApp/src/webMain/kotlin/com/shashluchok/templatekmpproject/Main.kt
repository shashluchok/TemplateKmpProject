package com.shashluchok.templatekmpproject

import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.window.ComposeViewport
import com.shashluchok.templatekmpproject.presentation.navigation.AppContent

@OptIn(ExperimentalComposeUiApi::class)
fun main() {
    ComposeViewport {
        AppContent()
    }
}
