package dev.lincforge.benchtarget.core

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class OrdersPolicyTest {

    @Test
    fun `all orders lists Order 101 through Order 108`() {
        assertEquals(8, OrdersPolicy.all.size)
        assertEquals("Order #101", OrdersPolicy.all.first())
        assertEquals("Order #108", OrdersPolicy.all.last())
    }

    @Test
    fun `activeOrders removes the archived order`() {
        assertEquals(8, OrdersPolicy.activeOrders(null).size)
        val filtered = OrdersPolicy.activeOrders("Order #104")
        assertEquals(7, filtered.size)
        assertFalse(filtered.contains("Order #104"))
        assertTrue(filtered.contains("Order #103"))
        assertTrue(filtered.contains("Order #105"))
    }
}
