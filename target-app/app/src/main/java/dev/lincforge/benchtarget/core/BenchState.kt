package dev.lincforge.benchtarget.core

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/** SPEC.md § Screens — the seven screens; `key` is the state.json value. */
enum class Screen(val key: String) {
    HOME("home"),
    CATALOG("catalog"),
    DETAIL("detail"),
    FORM("form"),
    ABOUT("about"),
    DIAGNOSTICS("diagnostics"),
    CHECKOUT("checkout"),
}

@Serializable
data class FormResult(
    val name: String,
    val tier: String,
    val subscribed: Boolean,
)

/**
 * SPEC.md § State contract: serialized to getExternalFilesDir(null)/state.json
 * after every significant state change. Nullable fields stay absent until the
 * first relevant interaction.
 */
@Serializable
data class BenchState(
    val screen: String,
    val selectedItem: String? = null,
    val lastFormResult: FormResult? = null,
    val launchCount: Int? = null,
)

object StateJson {
    private val json = Json {
        encodeDefaults = true
        explicitNulls = false
    }

    fun encode(state: BenchState): String = json.encodeToString(BenchState.serializer(), state)
}
