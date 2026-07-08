package dev.lincforge.benchtarget.core

/**
 * SPEC.md § Screens 3, crash ground truth (task b5): Export on "Item 013" ONLY
 * throws an uncaught IllegalStateException("export buffer not initialized").
 */
object ExportPolicy {
    const val CRASH_ITEM = "Item 013"

    fun export(item: String) {
        check(item != CRASH_ITEM) { "export buffer not initialized" }
    }
}
