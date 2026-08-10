package com.shashluchok.templatekmpproject.presentation.theme

import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.Easing
import androidx.compose.runtime.staticCompositionLocalOf

internal data class Motion(
    val duration: MotionDuration = MotionDuration(),
    val easing: MotionEasing = MotionEasing(),
) {
    companion object {
        val DEFAULT = Motion()
    }
}

@Suppress("MagicNumber")
internal data class MotionDuration(
    val instant: Int = 100,
    val quick: Int = 200,
    val standard: Int = 350,
    val deliberate: Int = 750,
)

@Suppress("MagicNumber")
internal data class MotionEasing(
    val standard: Easing = CubicBezierEasing(0.2f, 0f, 0f, 1f),
    val emphasizedDecelerate: Easing = CubicBezierEasing(0.05f, 0.7f, 0.1f, 1f),
    val emphasizedAccelerate: Easing = CubicBezierEasing(0.3f, 0f, 0.8f, 0.15f),
)

internal val LocalMotion = staticCompositionLocalOf<Motion> { error("No motion tokens provided") }
