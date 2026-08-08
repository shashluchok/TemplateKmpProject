package com.shashluchok.templatekmpproject.presentation.theme

import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

internal data class Dimens(
    val padding: Padding = Padding(),
    val radius: Radius = Radius(),
    val iconSize: IconSize = IconSize(),
    val elevation: Elevation = Elevation(),
    val border: Border = Border(),
) {
    companion object {
        val DEFAULT = Dimens(
            padding =
                Padding(
                    tiny = 2.dp,
                    extraSmall = 4.dp,
                    small = 8.dp,
                    medium = 16.dp,
                    large = 24.dp,
                    extraLarge = 32.dp,
                ),
            radius =
                Radius(
                    small = 8.dp,
                    medium = 12.dp,
                    large = 16.dp,
                    extraLarge = 24.dp,
                ),
            iconSize =
                IconSize(
                    small = 16.dp,
                    medium = 24.dp,
                    large = 32.dp,
                    extraLarge = 48.dp,
                ),
            elevation =
                Elevation(
                    small = 2.dp,
                    medium = 4.dp,
                    large = 8.dp,
                ),
            border =
                Border(
                    thin = 1.dp,
                    thick = 2.dp,
                ),
        )
    }
}

internal data class Padding(
    val tiny: Dp = Dp.Unspecified,
    val extraSmall: Dp = Dp.Unspecified,
    val small: Dp = Dp.Unspecified,
    val medium: Dp = Dp.Unspecified,
    val large: Dp = Dp.Unspecified,
    val extraLarge: Dp = Dp.Unspecified,
)

internal data class Radius(
    val small: Dp = Dp.Unspecified,
    val medium: Dp = Dp.Unspecified,
    val large: Dp = Dp.Unspecified,
    val extraLarge: Dp = Dp.Unspecified,
)

internal data class IconSize(
    val small: Dp = Dp.Unspecified,
    val medium: Dp = Dp.Unspecified,
    val large: Dp = Dp.Unspecified,
    val extraLarge: Dp = Dp.Unspecified,
)

internal data class Elevation(
    val small: Dp = Dp.Unspecified,
    val medium: Dp = Dp.Unspecified,
    val large: Dp = Dp.Unspecified,
)

internal data class Border(
    val thin: Dp = Dp.Unspecified,
    val thick: Dp = Dp.Unspecified,
)

internal val LocalDimens = staticCompositionLocalOf<Dimens> { error("No dimens provided") }
