package com.shashluchok.templatekmpproject.presentation.screen.main

import com.shashluchok.templatekmpproject.presentation.screen.BaseViewModel
import kotlinx.coroutines.flow.MutableStateFlow

internal class MainViewModel : BaseViewModel<MainViewModel.State, MainViewModel.Action>() {
    data object State

    sealed interface Action

    override val mutableStateFlow: MutableStateFlow<State> = MutableStateFlow(State)

    override fun onAction(action: Action) {
        when (action) {
            else -> {}
        }
    }
}
