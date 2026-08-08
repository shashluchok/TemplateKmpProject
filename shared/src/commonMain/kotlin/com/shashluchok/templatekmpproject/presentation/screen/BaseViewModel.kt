package com.shashluchok.templatekmpproject.presentation.screen

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

internal abstract class BaseViewModel<State, Action> : ViewModel() {
    val stateFlow: StateFlow<State> get() = mutableStateFlow

    protected var state: State
        get() = stateFlow.value
        set(value) {
            mutableStateFlow.value = value
        }

    protected abstract val mutableStateFlow: MutableStateFlow<State>

    abstract fun onAction(action: Action)
}
