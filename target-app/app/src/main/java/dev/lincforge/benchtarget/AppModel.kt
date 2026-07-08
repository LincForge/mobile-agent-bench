package dev.lincforge.benchtarget

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import dev.lincforge.benchtarget.core.BenchState
import dev.lincforge.benchtarget.core.FormLogic
import dev.lincforge.benchtarget.core.FormResult
import dev.lincforge.benchtarget.core.Screen
import dev.lincforge.benchtarget.core.StateJson
import java.io.File

const val LOG_TAG = "BenchTarget"

/** SPEC.md § State contract: state.json rewritten after every significant state change. */
class StateFileWriter(private val dir: File?) {
    fun write(state: BenchState) {
        dir?.let { File(it, "state.json").writeText(StateJson.encode(state)) }
    }
}

/**
 * Single source of UI state for the single-activity app. Every mutation
 * persists the spec state contract and logs at the frozen tag.
 */
class AppModel(
    private val writer: StateFileWriter,
    private val launchCount: Int,
    val seeded: Boolean,
    val retrySyncVisible: Boolean,
) {
    var screen by mutableStateOf(Screen.HOME)
        private set
    var selectedItem by mutableStateOf<String?>(null)
        private set
    var lastFormResult by mutableStateOf<FormResult?>(null)
        private set
    var formResultText by mutableStateOf<String?>(null)
        private set

    fun persist() {
        writer.write(
            BenchState(
                screen = screen.key,
                selectedItem = selectedItem,
                lastFormResult = lastFormResult,
                launchCount = launchCount,
            ),
        )
    }

    fun navigate(target: Screen) {
        Log.d(LOG_TAG, "screen transition: ${screen.key} -> ${target.key}")
        screen = target
        persist()
    }

    fun openDetail(item: String) {
        selectedItem = item
        navigate(Screen.DETAIL)
    }

    fun submitForm(name: String, tier: String, subscribed: Boolean) {
        val submission = FormLogic.submit(name, tier, subscribed, seeded)
        lastFormResult = submission.result
        formResultText = submission.resultText
        Log.d(LOG_TAG, "form submitted: ${submission.resultText}")
        persist()
    }

    /** Back mirrors the forward nav graph; HOME is handled by the activity (finish). */
    fun back() {
        val target = when (screen) {
            Screen.DETAIL -> Screen.CATALOG
            Screen.DIAGNOSTICS -> Screen.ABOUT
            else -> Screen.HOME
        }
        navigate(target)
    }
}
