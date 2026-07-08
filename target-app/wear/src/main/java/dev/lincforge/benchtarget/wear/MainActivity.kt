package dev.lincforge.benchtarget.wear

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.wear.compose.material.Chip
import androidx.wear.compose.material.ChipDefaults
import androidx.wear.compose.material.MaterialTheme
import androidx.wear.compose.material.Text
import java.io.File

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        writeState(0)
        setContent {
            MaterialTheme {
                var pings by remember { mutableIntStateOf(0) }
                Column(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterVertically),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text("BenchTarget", style = MaterialTheme.typography.title2)
                    Chip(
                        onClick = {
                            pings += 1
                            Log.d("BenchTarget", "ping: $pings")
                            writeState(pings)
                        },
                        label = { Text("Ping") },
                        colors = ChipDefaults.primaryChipColors(),
                    )
                    Text(WearLogic.pingsText(pings))
                }
            }
        }
    }

    private fun writeState(pings: Int) {
        getExternalFilesDir(null)?.let { File(it, "state.json").writeText(WearLogic.stateJson(pings)) }
    }
}
