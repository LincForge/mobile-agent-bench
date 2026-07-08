package dev.lincforge.benchtarget.core

data class FormSubmission(val resultText: String, val result: FormResult)

/** SPEC.md § Screens 4: `Registered <name> (<tier>, subscribed=<true|false>)`. */
object FormLogic {

    fun submit(name: String, tier: String, subscribed: Boolean, seeded: Boolean): FormSubmission {
        // SPEC.md § Seeded flavor defect 1 (frozen): the Tier dropdown selection
        // is not propagated — seeded builds always register "Basic".
        val effectiveTier = if (seeded) "Basic" else tier
        val result = FormResult(name, effectiveTier, subscribed)
        return FormSubmission(
            resultText = "Registered $name ($effectiveTier, subscribed=$subscribed)",
            result = result,
        )
    }
}
