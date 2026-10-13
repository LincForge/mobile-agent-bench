package dev.lincforge.benchtarget.wear

/**
 * SPEC.md § Wear module: counter text + the watch's state-file analog (b8),
 * plus Burst mode (b11) and watch distractor node token (a6).
 */
object WearLogic {

    const val WATCH_NODE_TOKEN = "WATCH-NODE-999"

    fun nodeTokenText(): String = "Node token: $WATCH_NODE_TOKEN"

    fun modeLabel(burstMode: Boolean): String = if (burstMode) "Mode: Burst" else "Mode: Standard"

    fun pingStep(burstMode: Boolean): Int = if (burstMode) 5 else 1

    fun pingsText(pings: Int, burstMode: Boolean = false): String =
        if (burstMode) "Pings: $pings (Burst)" else "Pings: $pings"

    fun stateJson(pings: Int, burstMode: Boolean = false): String =
        if (burstMode) {
            """{"screen": "main", "pings": $pings, "mode": "burst"}"""
        } else {
            """{"screen": "main", "pings": $pings}"""
        }
}
