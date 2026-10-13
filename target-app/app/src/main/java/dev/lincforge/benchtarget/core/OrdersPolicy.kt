package dev.lincforge.benchtarget.core

/**
 * Task a5 (longpress-context-archive): Order #101 .. Order #108, with a single
 * active archive slot persisted to state.json under `archivedOrder`.
 */
object OrdersPolicy {

    val all: List<String> = (101..108).map { "Order #$it" }

    fun activeOrders(archivedOrder: String?): List<String> =
        all.filter { it != archivedOrder }
}
