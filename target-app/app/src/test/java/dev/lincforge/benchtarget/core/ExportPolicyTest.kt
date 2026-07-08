package dev.lincforge.benchtarget.core

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

/**
 * SPEC.md § Screens 3 (crash ground truth, task b5): Export on "Item 013" ONLY
 * throws IllegalStateException("export buffer not initialized").
 */
class ExportPolicyTest {

    @Test
    fun `export on Item 013 throws the frozen exception`() {
        val e = assertFailsWith<IllegalStateException> { ExportPolicy.export("Item 013") }
        assertEquals("export buffer not initialized", e.message)
    }

    @Test
    fun `export on every other item succeeds`() {
        CatalogItems.all.filterNot { it == "Item 013" }.forEach { ExportPolicy.export(it) }
    }
}
