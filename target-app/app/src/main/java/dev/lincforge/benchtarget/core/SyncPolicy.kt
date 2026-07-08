package dev.lincforge.benchtarget.core

/**
 * SPEC.md § Screens 6, flake ground truth (task b6): the sync component's
 * initialization is skipped depending on the persisted cold-start counter as it
 * stood BEFORE this launch's increment — from cleared data, launches #3 and #5
 * (prior counts 2 and 4) are missing the "Retry sync" button. Not timing, not
 * network, not randomness.
 */
object SyncPolicy {
    private val initSkipValues = setOf(2, 4)

    fun showRetrySync(priorColdStarts: Int): Boolean = priorColdStarts % 5 !in initSkipValues
}
