package dev.lincforge.benchtarget

import kotlin.math.min
import kotlin.math.roundToInt

/**
 * SPEC.md § Screens 7, runtime-state ground truth (task c10): applyDiscount()
 * computes an internal, never-displayed, never-logged discountFactor. The
 * displayed total is rounded to WHOLE dollars so the factor cannot be recovered
 * by back-division from the UI. The class and method names are part of the
 * frozen contract — runtime inspection targets CheckoutViewModel.applyDiscount().
 */
class CheckoutViewModel {

    private var currentQuantity: Int = 1

    val quantity: Int
        get() = currentQuantity

    fun setQuantity(value: Int) {
        currentQuantity = value.coerceIn(1, 10)
    }

    fun applyDiscount(): String {
        val discountFactor = 1.0 - min(currentQuantity, 10) * 0.035
        val totalDollars = (UNIT_PRICE * currentQuantity * discountFactor).roundToInt()
        return "$$totalDollars"
    }

    companion object {
        const val UNIT_PRICE = 9.37
    }
}
