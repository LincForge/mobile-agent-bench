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
}
