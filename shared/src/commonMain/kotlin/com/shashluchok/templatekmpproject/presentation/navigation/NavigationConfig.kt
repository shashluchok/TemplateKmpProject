package com.shashluchok.templatekmpproject.presentation.navigation

import androidx.navigation3.runtime.NavKey
import androidx.savedstate.serialization.SavedStateConfiguration
import com.shashluchok.templatekmpproject.presentation.navigation.destination.Main
import kotlinx.serialization.modules.SerializersModule
import kotlinx.serialization.modules.polymorphic

private val navigationSerializers = SerializersModule {
    polymorphic(NavKey::class) {
        subclass(Main::class, Main.serializer())
    }
}

internal val navigationConfig = SavedStateConfiguration {
    serializersModule = navigationSerializers
}
