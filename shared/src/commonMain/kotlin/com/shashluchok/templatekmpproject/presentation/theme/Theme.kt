package com.shashluchok.templatekmpproject.presentation.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider

private val LightColorScheme =
    lightColorScheme(
        primary = mdThemeLightPrimary,
        onPrimary = mdThemeLightOnPrimary,
        primaryContainer = mdThemeLightPrimaryContainer,
        onPrimaryContainer = mdThemeLightOnPrimaryContainer,
        secondary = mdThemeLightSecondary,
        onSecondary = mdThemeLightOnSecondary,
        secondaryContainer = mdThemeLightSecondaryContainer,
        onSecondaryContainer = mdThemeLightOnSecondaryContainer,
        tertiary = mdThemeLightTertiary,
        onTertiary = mdThemeLightOnTertiary,
        tertiaryContainer = mdThemeLightTertiaryContainer,
        onTertiaryContainer = mdThemeLightOnTertiaryContainer,
        error = mdThemeLightError,
        onError = mdThemeLightOnError,
        errorContainer = mdThemeLightErrorContainer,
        onErrorContainer = mdThemeLightOnErrorContainer,
        outline = mdThemeLightOutline,
        background = mdThemeLightBackground,
        onBackground = mdThemeLightOnBackground,
        surface = mdThemeLightSurface,
        onSurface = mdThemeLightOnSurface,
        surfaceVariant = mdThemeLightSurfaceVariant,
        onSurfaceVariant = mdThemeLightOnSurfaceVariant,
        inverseSurface = mdThemeLightInverseSurface,
        inverseOnSurface = mdThemeLightInverseOnSurface,
        inversePrimary = mdThemeLightInversePrimary,
        surfaceTint = mdThemeLightSurfaceTint,
        outlineVariant = mdThemeLightOutlineVariant,
        scrim = mdThemeLightScrim,
        surfaceBright = mdThemeLightSurfaceBright,
        surfaceContainer = mdThemeLightSurfaceContainer,
        surfaceContainerHigh = mdThemeLightSurfaceContainerHigh,
        surfaceContainerHighest = mdThemeLightSurfaceContainerHighest,
        surfaceContainerLow = mdThemeLightSurfaceContainerLow,
        surfaceContainerLowest = mdThemeLightSurfaceContainerLowest,
        surfaceDim = mdThemeLightSurfaceDim,
        primaryFixed = mdThemeLightPrimaryFixed,
        primaryFixedDim = mdThemeLightPrimaryFixedDim,
        onPrimaryFixed = mdThemeLightOnPrimaryFixed,
        onPrimaryFixedVariant = mdThemeLightOnPrimaryFixedVariant,
        secondaryFixed = mdThemeLightSecondaryFixed,
        secondaryFixedDim = mdThemeLightSecondaryFixedDim,
        onSecondaryFixed = mdThemeLightOnSecondaryFixed,
        onSecondaryFixedVariant = mdThemeLightOnSecondaryFixedVariant,
        tertiaryFixed = mdThemeLightTertiaryFixed,
        tertiaryFixedDim = mdThemeLightTertiaryFixedDim,
        onTertiaryFixed = mdThemeLightOnTertiaryFixed,
        onTertiaryFixedVariant = mdThemeLightOnTertiaryFixedVariant,
    )

private val DarkColorScheme =
    darkColorScheme(
        primary = mdThemeDarkPrimary,
        onPrimary = mdThemeDarkOnPrimary,
        primaryContainer = mdThemeDarkPrimaryContainer,
        onPrimaryContainer = mdThemeDarkOnPrimaryContainer,
        secondary = mdThemeDarkSecondary,
        onSecondary = mdThemeDarkOnSecondary,
        secondaryContainer = mdThemeDarkSecondaryContainer,
        onSecondaryContainer = mdThemeDarkOnSecondaryContainer,
        tertiary = mdThemeDarkTertiary,
        onTertiary = mdThemeDarkOnTertiary,
        tertiaryContainer = mdThemeDarkTertiaryContainer,
        onTertiaryContainer = mdThemeDarkOnTertiaryContainer,
        error = mdThemeDarkError,
        onError = mdThemeDarkOnError,
        errorContainer = mdThemeDarkErrorContainer,
        onErrorContainer = mdThemeDarkOnErrorContainer,
        outline = mdThemeDarkOutline,
        background = mdThemeDarkBackground,
        onBackground = mdThemeDarkOnBackground,
        surface = mdThemeDarkSurface,
        onSurface = mdThemeDarkOnSurface,
        surfaceVariant = mdThemeDarkSurfaceVariant,
        onSurfaceVariant = mdThemeDarkOnSurfaceVariant,
        inverseSurface = mdThemeDarkInverseSurface,
        inverseOnSurface = mdThemeDarkInverseOnSurface,
        inversePrimary = mdThemeDarkInversePrimary,
        surfaceTint = mdThemeDarkSurfaceTint,
        outlineVariant = mdThemeDarkOutlineVariant,
        scrim = mdThemeDarkScrim,
        surfaceBright = mdThemeDarkSurfaceBright,
        surfaceContainer = mdThemeDarkSurfaceContainer,
        surfaceContainerHigh = mdThemeDarkSurfaceContainerHigh,
        surfaceContainerHighest = mdThemeDarkSurfaceContainerHighest,
        surfaceContainerLow = mdThemeDarkSurfaceContainerLow,
        surfaceContainerLowest = mdThemeDarkSurfaceContainerLowest,
        surfaceDim = mdThemeDarkSurfaceDim,
        primaryFixed = mdThemeDarkPrimaryFixed,
        primaryFixedDim = mdThemeDarkPrimaryFixedDim,
        onPrimaryFixed = mdThemeDarkOnPrimaryFixed,
        onPrimaryFixedVariant = mdThemeDarkOnPrimaryFixedVariant,
        secondaryFixed = mdThemeDarkSecondaryFixed,
        secondaryFixedDim = mdThemeDarkSecondaryFixedDim,
        onSecondaryFixed = mdThemeDarkOnSecondaryFixed,
        onSecondaryFixedVariant = mdThemeDarkOnSecondaryFixedVariant,
        tertiaryFixed = mdThemeDarkTertiaryFixed,
        tertiaryFixedDim = mdThemeDarkTertiaryFixedDim,
        onTertiaryFixed = mdThemeDarkOnTertiaryFixed,
        onTertiaryFixedVariant = mdThemeDarkOnTertiaryFixedVariant,
    )

@Composable
internal fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dimens: Dimens = Dimens.DEFAULT,
    motion: Motion = Motion.DEFAULT,
    content: @Composable () -> Unit,
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = ComposeTypography,
    ) {
        CompositionLocalProvider(
            LocalDimens provides dimens,
            LocalMotion provides motion,
        ) {
            content()
        }
    }
}
