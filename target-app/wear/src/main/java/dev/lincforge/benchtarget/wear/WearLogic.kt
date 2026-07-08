package dev.lincforge.benchtarget.wear

/** SPEC.md § Wear module: counter text + the watch's state-file analog. */
object WearLogic {

    fun pingsText(pings: Int): String = "Pings: $pings"

    fun stateJson(pings: Int): String = """{"screen": "main", "pings": $pings}"""
}
