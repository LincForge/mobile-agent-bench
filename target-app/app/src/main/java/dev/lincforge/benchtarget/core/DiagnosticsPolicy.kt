package dev.lincforge.benchtarget.core

/**
 * Ground-truth constants and policies for v3 Diagnostics tasks:
 * - a6 (multi-device-disambiguation): phone node token PHONE-NODE-742
 * - b9 (silent-error-log-attribution): generic UI error vs structured logcat cause
 * - b10 (main-thread-stall-isolation): IndexRebuilder.rebuildBlocking() 1850ms main-thread block
 */
object DiagnosticsPolicy {

    const val PHONE_NODE_TOKEN = "PHONE-NODE-742"
    const val HEALTH_CHECK_UI_TEXT = "Health check failed (code E-400)"
    const val HEALTH_CHECK_LOG_MESSAGE =
        "health_check E-400: clock_skew_ms=4720 exceeds max_skew_ms=1000 (upstream=time-west-2)"

    fun nodeTokenText(): String = "Node token: $PHONE_NODE_TOKEN"
}

object IndexRebuilder {

    const val STALL_MS = 1850L
    const val STALL_LOG_MESSAGE =
        "stall_detected op=rebuild_index blocked_ms=1850 component=IndexRebuilder"

    fun verifyCache(): String = "Maintenance complete"

    fun compactDb(): String = "Maintenance complete"

    fun rebuildBlocking(sleepFn: (Long) -> Unit = { Thread.sleep(it) }): String {
        sleepFn(STALL_MS)
        return "Maintenance complete"
    }
}
