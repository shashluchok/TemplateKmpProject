package com.shashluchok.templatekmpproject.presentation.navigation

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation3.runtime.entryProvider
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.navigation3.ui.NavDisplay
import com.shashluchok.templatekmpproject.di.appModules
import com.shashluchok.templatekmpproject.presentation.navigation.destination.Main
import com.shashluchok.templatekmpproject.presentation.screen.main.MainScreen
import com.shashluchok.templatekmpproject.presentation.theme.AppTheme
import org.koin.compose.KoinApplication
import org.koin.core.module.Module
import org.koin.dsl.koinConfiguration

@Composable
fun AppContent(
    modifier: Modifier = Modifier,
    platformModule: Module? = null,
) {
    KoinApplication(
        configuration = koinConfiguration {
            modules(
                listOfNotNull(
                    platformModule,
                ) + appModules,
            )
        },
    ) {
        AppTheme {
            val backStack = rememberNavBackStack(
                configuration = navigationConfig,
                elements = arrayOf(Main),
            )

            NavDisplay(
                modifier = modifier,
                backStack = backStack,
                onBack = backStack::removeLastOrNull,
                entryProvider = entryProvider {
                    entry<Main> {
                        MainScreen(
                            modifier = Modifier.fillMaxSize(),
                        )
                    }
                },
            )
        }
    }
}
