package dev.lincforge.benchtarget.wear

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/**
 * SPEC.md § Wear module (task b8): counter text `Pings: <n>` (verify regex
 * `Pings:\s*3`) and a state-file analog on the watch's external files dir.
 */
class WearLogicTest {

    @Test
    fun `counter text matches the b8 verify regex at three pings`() {
        val text = WearLogic.pingsText(3)
        assertEquals("Pings: 3", text)
        assertTrue(Regex("Pings:\\s*3").containsMatchIn(text))
    }

    @Test
    fun `state json is single line with screen and pings`() {
        val json = WearLogic.stateJson(pings = 2)
        assertFalse(json.contains("\n"))
        assertTrue(Regex("\"screen\": *\"main\"").containsMatchIn(json))
        assertTrue(Regex("\"pings\": *2").containsMatchIn(json))
    }

    @Test
    fun `watch node token matches a6 distractor ground truth`() {
        assertEquals("WATCH-NODE-999", WearLogic.WATCH_NODE_TOKEN)
        assertEquals("Node token: WATCH-NODE-999", WearLogic.nodeTokenText())
    }

    @Test
    fun `burst mode increments by 5 and formats Pings 15 Burst`() {
        assertEquals("Mode: Standard", WearLogic.modeLabel(false))
        assertEquals("Mode: Burst", WearLogic.modeLabel(true))
        assertEquals(1, WearLogic.pingStep(false))
        assertEquals(5, WearLogic.pingStep(true))
        val text = WearLogic.pingsText(15, burstMode = true)
        assertEquals("Pings: 15 (Burst)", text)
        val json = WearLogic.stateJson(pings = 15, burstMode = true)
        assertTrue(Regex("\"pings\": *15").containsMatchIn(json))
        assertTrue(Regex("\"mode\": *\"burst\"").containsMatchIn(json))
    }
}
