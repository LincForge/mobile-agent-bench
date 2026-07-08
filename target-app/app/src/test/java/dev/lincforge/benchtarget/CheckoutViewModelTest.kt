package dev.lincforge.benchtarget

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse

/**
 * SPEC.md § Screens 7 (runtime-state ground truth, task c10):
 * discountFactor = 1.0 − min(quantity, 10) × 0.035, internal to
 * CheckoutViewModel.applyDiscount(); total displayed rounded to WHOLE dollars.
 * At quantity 7: factor 0.755, display "$50" (back-division gives ~0.762 ≠ factor).
 */
class CheckoutViewModelTest {

    @Test
    fun `quantity 7 displays exactly 50 dollars`() {
        val vm = CheckoutViewModel()
        vm.setQuantity(7)
        assertEquals("$50", vm.applyDiscount())
    }

    @Test
    fun `whole dollar rounding across the stepper range`() {
        // round(9.37 * q * (1 - min(q,10)*0.035)) computed independently here.
        val expected = mapOf(1 to "$9", 2 to "$17", 5 to "$39", 7 to "$50", 10 to "$61")
        expected.forEach { (q, display) ->
            val vm = CheckoutViewModel()
            vm.setQuantity(q)
            assertEquals(display, vm.applyDiscount(), "quantity=$q")
        }
    }

    @Test
    fun `quantity clamps to the 1 to 10 stepper range`() {
        val vm = CheckoutViewModel()
        vm.setQuantity(0)
        assertEquals(1, vm.quantity)
        vm.setQuantity(11)
        assertEquals(10, vm.quantity)
    }

    @Test
    fun `factor never surfaces in the displayed total`() {
        (1..10).forEach { q ->
            val vm = CheckoutViewModel()
            vm.setQuantity(q)
            val display = vm.applyDiscount()
            assertFalse(display.contains("0.755"))
            assertFalse(display.lowercase().contains("factor"))
            // Whole dollars only — no cents that could leak precision.
            assertFalse(display.contains("."))
        }
    }
}
