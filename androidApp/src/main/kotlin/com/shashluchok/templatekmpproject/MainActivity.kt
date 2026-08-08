package com.shashluchok.templatekmpproject

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.shashluchok.templatekmpproject.di.androidModule
import com.shashluchok.templatekmpproject.presentation.navigation.AppContent

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)

        setContent {
            AppContent(platformModule = androidModule)
        }
    }
}
