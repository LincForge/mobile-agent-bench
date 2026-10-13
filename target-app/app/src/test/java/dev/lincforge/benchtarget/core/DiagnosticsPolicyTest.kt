package dev.lincforge.benchtarget.core

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class DiagnosticsPolicyTest {

    @Test
    fun `phone node token matches a6 ground truth`() {
        assertEquals("PHONE-NODE-742", DiagnosticsPolicy.PHONE_NODE_TOKEN)
        assertEquals("Node token: PHONE-NODE-742", DiagnosticsPolicy.nodeTokenText())
    }

    @Test
    fun `b9 health check UI text omits log-only cause and skew`() {
        val ui = DiagnosticsPolicy.HEALTH_CHECK_UI_TEXT
        assertEquals("Health check failed (code E-400)", ui)
        assertFalse(ui.contains("clock_skew"))
        assertFalse(ui.contains("4720"))
        assertFalse(ui.contains("time-west-2"))

        val log = DiagnosticsPolicy.HEALTH_CHECK_LOG_MESSAGE
        assertTrue(log.contains("clock_skew_ms=4720"))
        assertTrue(log.contains("upstream=time-west-2"))
    }

    @Test
    fun `b10 IndexRebuilder blocks for 1850ms and emits structured stall message`() {
        var sleptMs = 0L
        val status = IndexRebuilder.rebuildBlocking { ms -> sleptMs = ms }
        assertEquals(1850L, sleptMs)
        assertEquals("Maintenance complete", status)
        assertTrue(IndexRebuilder.STALL_LOG_MESSAGE.contains("op=rebuild_index"))
        assertTrue(IndexRebuilder.STALL_LOG_MESSAGE.contains("blocked_ms=1850"))
        assertTrue(IndexRebuilder.STALL_LOG_MESSAGE.contains("component=IndexRebuilder"))
    }
}
