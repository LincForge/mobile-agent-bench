package dev.lincforge.benchtarget.core

import kotlin.test.Test
import kotlin.test.assertEquals

/** SPEC.md § Screens 2: 100 items, three-digit zero-padded names. */
class CatalogItemsTest {

    @Test
    fun `catalog has exactly 100 zero-padded items`() {
        assertEquals(100, CatalogItems.all.size)
        assertEquals("Item 001", CatalogItems.all.first())
        assertEquals("Item 013", CatalogItems.all[12])
        assertEquals("Item 073", CatalogItems.all[72])
        assertEquals("Item 100", CatalogItems.all.last())
    }
}
