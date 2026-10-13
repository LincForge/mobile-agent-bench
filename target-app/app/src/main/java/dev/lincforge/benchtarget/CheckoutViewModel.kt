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

    /**
     * Task c11 (runtime-promo-signature): computes an internal, never-displayed,
     * never-logged `auditToken` local variable while returning only generic
     * confirmation text to the UI. Kept flat (3 statements) so JDB/Spectra
     * `method_locals` reaches `auditToken` within default `max_steps`.
     */
    fun redeemPromo(code: String): String {
        val normalized = code.trim().uppercase()
        val auditToken = formatAuditToken(currentQuantity, normalized)
        return if (auditToken.startsWith("AUD-")) "Promo applied" else "Invalid promo"
    }

    internal fun formatAuditToken(quantity: Int, normalized: String): String {
        val raw = normalized.fold(quantity * 97) { acc, ch ->
            (acc * 31 + ch.code) % 10000
        }
        val checksum = (raw + 7555) % 10000
        return "AUD-$quantity-$normalized-${checksum.toString().padStart(4, '0')}"
    }

    companion object {
        const val UNIT_PRICE = 9.37
    }
}
