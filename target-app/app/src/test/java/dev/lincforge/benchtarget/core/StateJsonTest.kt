package dev.lincforge.benchtarget.core

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/**
 * SPEC.md § State contract: single-line JSON, fields absent until first
 * relevant interaction. Harness task YAMLs grep with `"key": *value` patterns
 * (a2, a3) — compact JSON must match them.
 */
class StateJsonTest {

    @Test
    fun `initial state omits fields not yet touched`() {
        val json = StateJson.encode(BenchState(screen = "home", launchCount = 1))
        assertFalse(json.contains("selectedItem"))
        assertFalse(json.contains("lastFormResult"))
        assertTrue(json.contains("\"screen\":\"home\""))
        assertTrue(json.contains("\"launchCount\":1"))
    }

    @Test
    fun `encoded state is a single line`() {
        val json = StateJson.encode(
            BenchState(
                screen = "form",
                selectedItem = "Item 073",
                lastFormResult = FormResult("Avery Quinn", "Pro", true),
                launchCount = 4,
            ),
        )
        assertFalse(json.contains("\n"))
    }

    @Test
    fun `full state matches the harness grep patterns from a2 and a3`() {
        val json = StateJson.encode(
            BenchState(
                screen = "detail",
                selectedItem = "Item 073",
                lastFormResult = FormResult("Avery Quinn", "Pro", true),
                launchCount = 2,
            ),
        )
        // Exact verify regexes from tasks/a2-form-fill.yaml and a3-scroll-list.yaml.
        assertTrue(Regex("\"screen\": *\"detail\"").containsMatchIn(json))
        assertTrue(Regex("\"selectedItem\": *\"Item 073\"").containsMatchIn(json))
        assertTrue(json.contains("\"Avery Quinn\""))
        assertTrue(Regex("\"tier\": *\"Pro\"").containsMatchIn(json))
        assertTrue(Regex("\"subscribed\": *true").containsMatchIn(json))
    }

    @Test
    fun `screen keys cover the spec enum`() {
        val expected = listOf(
            "home", "catalog", "detail", "form", "about", "diagnostics", "checkout", "orders",
        )
        assertEquals(expected, Screen.entries.map { it.key })
    }

    @Test
    fun `archivedOrder is omitted when null and matches a5 grep pattern when set`() {
        val initial = StateJson.encode(BenchState(screen = "orders", launchCount = 1))
        assertFalse(initial.contains("archivedOrder"))

        val archived = StateJson.encode(
            BenchState(
                screen = "orders",
                archivedOrder = "Order #104",
                launchCount = 1,
            ),
        )
        assertTrue(Regex("\"screen\": *\"orders\"").containsMatchIn(archived))
        assertTrue(Regex("\"archivedOrder\": *\"Order #104\"").containsMatchIn(archived))
    }
}
