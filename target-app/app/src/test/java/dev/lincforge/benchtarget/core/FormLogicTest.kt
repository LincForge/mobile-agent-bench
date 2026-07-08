package dev.lincforge.benchtarget.core

import kotlin.test.Test
import kotlin.test.assertEquals

/**
 * SPEC.md § Screens 4 (form) + § Seeded flavor defect 1 (tier not propagated,
 * task c9): seeded builds always report "Basic" regardless of selection.
 */
class FormLogicTest {

    @Test
    fun `stock submit propagates the selected tier`() {
        val s = FormLogic.submit(name = "Avery Quinn", tier = "Pro", subscribed = true, seeded = false)
        assertEquals("Registered Avery Quinn (Pro, subscribed=true)", s.resultText)
        assertEquals(FormResult("Avery Quinn", "Pro", true), s.result)
    }

    @Test
    fun `stock submit with defaults`() {
        val s = FormLogic.submit(name = "x", tier = "Basic", subscribed = false, seeded = false)
        assertEquals("Registered x (Basic, subscribed=false)", s.resultText)
    }

    @Test
    fun `seeded submit drops the selected tier back to Basic`() {
        listOf("Pro", "Max").forEach { tier ->
            val s = FormLogic.submit(name = "Avery Quinn", tier = tier, subscribed = true, seeded = true)
            assertEquals("Registered Avery Quinn (Basic, subscribed=true)", s.resultText)
            assertEquals("Basic", s.result.tier)
        }
    }

    @Test
    fun `seeded defect leaves name and subscribed intact`() {
        val s = FormLogic.submit(name = "n", tier = "Max", subscribed = false, seeded = true)
        assertEquals(FormResult("n", "Basic", false), s.result)
    }
}
