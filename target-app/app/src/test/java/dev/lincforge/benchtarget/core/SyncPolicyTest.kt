package dev.lincforge.benchtarget.core

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/**
 * SPEC.md § Screens 6 (flake ground truth, task b6): "Retry sync" renders only
 * when launchCount % 5 ∉ {2, 4} at cold start, where the value checked is the
 * counter as persisted BEFORE this launch's increment. Operational contract:
 * from cleared data, launches #3 and #5 are missing the button — passes 3/5.
 */
class SyncPolicyTest {

    @Test
    fun `from cleared data launches 3 and 5 hide the retry button`() {
        // Launch #n reads prior persisted value n-1 (cleared data starts at 0).
        val visibleByLaunch = (1..5).map { n -> SyncPolicy.showRetrySync(priorColdStarts = n - 1) }
        assertEquals(listOf(true, true, false, true, false), visibleByLaunch)
    }

    @Test
    fun `pattern repeats every five launches`() {
        val first = (1..5).map { SyncPolicy.showRetrySync(it - 1) }
        val second = (6..10).map { SyncPolicy.showRetrySync(it - 1) }
        assertEquals(first, second)
    }

    @Test
    fun `formula matches the frozen modulo rule`() {
        (0..24).forEach { prior ->
            val expected = prior % 5 !in setOf(2, 4)
            assertEquals(expected, SyncPolicy.showRetrySync(prior), "prior=$prior")
        }
    }

    @Test
    fun `passes 3 of 5 from cleared data`() {
        val visible = (1..5).count { SyncPolicy.showRetrySync(it - 1) }
        assertEquals(3, visible)
        assertTrue(SyncPolicy.showRetrySync(0))
        assertFalse(SyncPolicy.showRetrySync(2))
        assertFalse(SyncPolicy.showRetrySync(4))
    }
}
