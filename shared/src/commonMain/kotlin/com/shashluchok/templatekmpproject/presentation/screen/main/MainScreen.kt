package com.shashluchok.templatekmpproject.presentation.screen.main

import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.koin.compose.viewmodel.koinViewModel

@Composable
internal fun MainScreen(
    modifier: Modifier = Modifier,
    viewModel: MainViewModel = koinViewModel(),
) {
    val state = viewModel.stateFlow.collectAsStateWithLifecycle().value
    MainScreen(
        modifier = modifier,
        state = state,
        onAction = viewModel::onAction,
    )
}

@Suppress("UnusedParameter")
@Composable
private fun MainScreen(
    state: MainViewModel.State,
    onAction: (MainViewModel.Action) -> Unit,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier,
    )
}
