package com.shashluchok.templatekmpproject.di

import com.shashluchok.templatekmpproject.presentation.screen.main.MainViewModel
import org.koin.core.module.dsl.viewModel
import org.koin.dsl.module

internal val viewModelModule = module {
    viewModel { MainViewModel() }
}
