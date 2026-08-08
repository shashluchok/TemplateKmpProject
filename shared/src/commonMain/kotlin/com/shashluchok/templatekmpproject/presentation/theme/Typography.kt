package com.shashluchok.templatekmpproject.presentation.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val bodySmall =
    TextStyle(
        fontSize = 12.sp,
        lineHeight = 16.sp,
    )

private val bodyMedium =
    TextStyle(
        fontSize = 14.sp,
        lineHeight = 20.sp,
    )

private val bodyLarge =
    TextStyle(
        fontSize = 16.sp,
        lineHeight = 24.sp,
    )

private val labelSmall =
    TextStyle(
        fontSize = 11.sp,
        lineHeight = 16.sp,
        fontWeight = FontWeight.Medium,
    )

private val labelMedium =
    TextStyle(
        fontSize = 12.sp,
        lineHeight = 16.sp,
        fontWeight = FontWeight.Medium,
    )

private val labelLarge =
    TextStyle(
        fontSize = 14.sp,
        lineHeight = 20.sp,
        fontWeight = FontWeight.Medium,
    )

private val titleSmall =
    TextStyle(
        fontSize = 14.sp,
        lineHeight = 20.sp,
        fontWeight = FontWeight.Medium,
    )

private val titleMedium =
    TextStyle(
        fontSize = 16.sp,
        lineHeight = 24.sp,
        fontWeight = FontWeight.Medium,
    )

private val titleLarge =
    TextStyle(
        fontSize = 22.sp,
        lineHeight = 28.sp,
    )

private val headlineSmall =
    TextStyle(
        fontSize = 24.sp,
        lineHeight = 32.sp,
    )

private val headlineMedium =
    TextStyle(
        fontSize = 28.sp,
        lineHeight = 36.sp,
    )

private val headlineLarge =
    TextStyle(
        fontSize = 32.sp,
        lineHeight = 40.sp,
    )

private val displaySmall =
    TextStyle(
        fontSize = 36.sp,
        lineHeight = 44.sp,
    )

private val displayMedium =
    TextStyle(
        fontSize = 45.sp,
        lineHeight = 52.sp,
    )

private val displayLarge =
    TextStyle(
        fontSize = 57.sp,
        lineHeight = 64.sp,
    )

internal val ComposeTypography =
    Typography(
        bodySmall = bodySmall,
        bodyMedium = bodyMedium,
        bodyLarge = bodyLarge,
        labelSmall = labelSmall,
        labelMedium = labelMedium,
        labelLarge = labelLarge,
        titleSmall = titleSmall,
        titleMedium = titleMedium,
        titleLarge = titleLarge,
        headlineSmall = headlineSmall,
        headlineMedium = headlineMedium,
        headlineLarge = headlineLarge,
        displaySmall = displaySmall,
        displayMedium = displayMedium,
        displayLarge = displayLarge,
    )
