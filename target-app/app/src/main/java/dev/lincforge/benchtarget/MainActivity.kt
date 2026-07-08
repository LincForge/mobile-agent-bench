package dev.lincforge.benchtarget

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.foundation.layout.fillMaxSize
import dev.lincforge.benchtarget.core.Screen
import dev.lincforge.benchtarget.ui.AboutScreen
import dev.lincforge.benchtarget.ui.CatalogScreen
import dev.lincforge.benchtarget.ui.CheckoutScreen
import dev.lincforge.benchtarget.ui.DetailScreen
import dev.lincforge.benchtarget.ui.DiagnosticsScreen
import dev.lincforge.benchtarget.ui.FormScreen
import dev.lincforge.benchtarget.ui.HomeScreen

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        LaunchTracker.onColdStart(getSharedPreferences("benchtarget", MODE_PRIVATE))
        val model = AppModel(
            writer = StateFileWriter(getExternalFilesDir(null)),
            launchCount = LaunchTracker.totalLaunches,
            seeded = BuildConfig.SEEDED,
            retrySyncVisible = LaunchTracker.retrySyncVisible,
        )
        model.persist()
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    BenchTargetApp(model)
                }
            }
        }
    }
}

@Composable
fun BenchTargetApp(model: AppModel) {
    BackHandler(enabled = model.screen != Screen.HOME) { model.back() }
    when (model.screen) {
        Screen.HOME -> HomeScreen(model)
        Screen.CATALOG -> CatalogScreen(model)
        Screen.DETAIL -> DetailScreen(model)
        Screen.FORM -> FormScreen(model)
        Screen.ABOUT -> AboutScreen(model)
        Screen.DIAGNOSTICS -> DiagnosticsScreen(model)
        Screen.CHECKOUT -> CheckoutScreen(model)
    }
}
