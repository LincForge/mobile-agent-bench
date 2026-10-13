package dev.lincforge.benchtarget.ui

import android.util.Log
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.unit.dp
import dev.lincforge.benchtarget.AppModel
import dev.lincforge.benchtarget.CheckoutViewModel
import dev.lincforge.benchtarget.LOG_TAG
import dev.lincforge.benchtarget.core.CatalogItems
import dev.lincforge.benchtarget.core.DiagnosticsPolicy
import dev.lincforge.benchtarget.core.ExportPolicy
import dev.lincforge.benchtarget.core.IndexRebuilder
import dev.lincforge.benchtarget.core.OrdersPolicy
import dev.lincforge.benchtarget.core.Screen

@Composable
private fun ScreenColumn(content: @Composable ColumnScopeAlias.() -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) { content() }
}

private typealias ColumnScopeAlias = androidx.compose.foundation.layout.ColumnScope

@Composable
fun HomeScreen(model: AppModel) {
    ScreenColumn {
        Text("BenchTarget", style = MaterialTheme.typography.headlineLarge)
        Button(onClick = { model.navigate(Screen.CATALOG) }, modifier = Modifier.fillMaxWidth()) { Text("Catalog") }
        Button(onClick = { model.navigate(Screen.FORM) }, modifier = Modifier.fillMaxWidth()) { Text("Form") }
        Button(onClick = { model.navigate(Screen.ABOUT) }, modifier = Modifier.fillMaxWidth()) { Text("About") }
        Button(onClick = { model.navigate(Screen.CHECKOUT) }, modifier = Modifier.fillMaxWidth()) { Text("Checkout") }
        Button(onClick = { model.navigate(Screen.ORDERS) }, modifier = Modifier.fillMaxWidth()) { Text("Orders") }
    }
}

@Composable
fun CatalogScreen(model: AppModel) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Catalog", style = MaterialTheme.typography.headlineMedium)
        LazyColumn(modifier = Modifier.fillMaxSize()) {
            items(CatalogItems.all) { item ->
                Text(
                    item,
                    style = MaterialTheme.typography.titleLarge,
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { model.openDetail(item) }
                        .padding(vertical = 16.dp, horizontal = 8.dp),
                )
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun OrdersScreen(model: AppModel) {
    var contextOrder by remember { mutableStateOf<String?>(null) }
    var confirmOrder by remember { mutableStateOf<String?>(null) }
    val active = OrdersPolicy.activeOrders(model.archivedOrder)

    Column(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Orders", style = MaterialTheme.typography.headlineMedium)
        Text("Long-press an order to open its action menu.")
        model.archivedOrder?.let { archived ->
            Text("Archived: $archived", style = MaterialTheme.typography.titleMedium)
        }
        LazyColumn(modifier = Modifier.fillMaxSize()) {
            items(active, key = { it }) { order ->
                Box(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        order,
                        style = MaterialTheme.typography.titleLarge,
                        modifier = Modifier
                            .fillMaxWidth()
                            .combinedClickable(
                                onClick = { /* standard tap is a no-op; archive requires long-press */ },
                                onLongClick = { contextOrder = order },
                            )
                            .padding(vertical = 14.dp, horizontal = 8.dp),
                    )
                    DropdownMenu(
                        expanded = contextOrder == order,
                        onDismissRequest = { contextOrder = null },
                    ) {
                        DropdownMenuItem(
                            text = { Text("Archive order") },
                            onClick = {
                                confirmOrder = order
                                contextOrder = null
                            },
                        )
                    }
                }
            }
        }
    }

    confirmOrder?.let { order ->
        AlertDialog(
            onDismissRequest = { confirmOrder = null },
            title = { Text("Archive $order?") },
            text = { Text("This removes $order from the active queue.") },
            confirmButton = {
                Button(onClick = {
                    model.archiveOrder(order)
                    confirmOrder = null
                }) {
                    Text("Confirm archive")
                }
            },
            dismissButton = {
                OutlinedButton(onClick = { confirmOrder = null }) {
                    Text("Cancel")
                }
            },
        )
    }
}

@Composable
fun DetailScreen(model: AppModel) {
    val item = model.selectedItem.orEmpty()
    ScreenColumn {
        Text(item, style = MaterialTheme.typography.headlineMedium)
        Text("Catalog entry for $item.")
        // SPEC.md § Screens 3: on "Item 013" this throw is deliberately uncaught
        // on the main thread — the frozen crash ground truth (task b5).
        Button(onClick = { ExportPolicy.export(item) }) { Text("Export") }
    }
}

@Composable
fun FormScreen(model: AppModel) {
    var name by remember { mutableStateOf("") }
    var subscribed by remember { mutableStateOf(false) }
    var tier by remember { mutableStateOf("Basic") }
    var tierMenuOpen by remember { mutableStateOf(false) }

    ScreenColumn {
        Text("Form", style = MaterialTheme.typography.headlineMedium)
        OutlinedTextField(
            value = name,
            onValueChange = { name = it },
            label = { Text("Name") },
            modifier = Modifier.fillMaxWidth(),
        )
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Subscribe")
            Spacer(Modifier.width(12.dp))
            Switch(checked = subscribed, onCheckedChange = { subscribed = it })
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Tier")
            Spacer(Modifier.width(12.dp))
            OutlinedButton(onClick = { tierMenuOpen = true }) { Text(tier) }
            DropdownMenu(expanded = tierMenuOpen, onDismissRequest = { tierMenuOpen = false }) {
                listOf("Basic", "Pro", "Max").forEach { option ->
                    DropdownMenuItem(
                        text = { Text(option) },
                        onClick = {
                            tier = option
                            tierMenuOpen = false
                        },
                    )
                }
            }
        }
        if (model.seeded) {
            // SPEC.md § Seeded flavor defect 2 (frozen): icon-only Submit with no
            // accessible label/contentDescription.
            Button(onClick = { model.submitForm(name, tier, subscribed) }) {
                Canvas(modifier = Modifier.size(20.dp)) {
                    val path = Path().apply {
                        moveTo(0f, 0f)
                        lineTo(size.width, size.height / 2f)
                        lineTo(0f, size.height)
                        close()
                    }
                    drawPath(path, color = androidx.compose.ui.graphics.Color.White)
                }
            }
        } else {
            Button(onClick = { model.submitForm(name, tier, subscribed) }) { Text("Submit") }
        }
        model.formResultText?.let { Text(it) }
    }
}

@Composable
fun AboutScreen(model: AppModel) {
    ScreenColumn {
        Text("About", style = MaterialTheme.typography.headlineMedium)
        Text("BenchTarget is a purpose-built benchmark target application. It has no network access, collects nothing, and exists so that agent runs are reproducible from source.")
        Button(onClick = { model.navigate(Screen.DIAGNOSTICS) }) { Text("Diagnostics") }
    }
}

@Composable
fun DiagnosticsScreen(model: AppModel) {
    var healthStatus by remember { mutableStateOf<String?>(null) }
    var maintenanceStatus by remember { mutableStateOf<String?>(null) }

    ScreenColumn {
        Text("Diagnostics", style = MaterialTheme.typography.headlineMedium)
        Text("Build channel: BENCH-STABLE")
        Text(DiagnosticsPolicy.nodeTokenText())
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Sync status", style = MaterialTheme.typography.titleMedium)
                Text(if (model.retrySyncVisible) "Sync idle" else "Sync unavailable")
                if (model.retrySyncVisible) {
                    // SPEC.md § Screens 6: rendered only when the sync component
                    // initialized this cold start (task b6 flake ground truth).
                    OutlinedButton(onClick = { /* no-op: sync is a stub */ }) { Text("Retry sync") }
                }
            }
        }
        Button(onClick = {
            Log.w(LOG_TAG, DiagnosticsPolicy.HEALTH_CHECK_LOG_MESSAGE)
            healthStatus = DiagnosticsPolicy.HEALTH_CHECK_UI_TEXT
        }) {
            Text("Run health check")
        }
        healthStatus?.let { Text(it) }
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Maintenance", style = MaterialTheme.typography.titleMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = {
                        Log.d(LOG_TAG, "maintenance op=verify_cache blocked_ms=12")
                        maintenanceStatus = IndexRebuilder.verifyCache()
                    }) {
                        Text("Verify cache")
                    }
                    OutlinedButton(onClick = {
                        Log.d(LOG_TAG, "maintenance op=compact_db blocked_ms=18")
                        maintenanceStatus = IndexRebuilder.compactDb()
                    }) {
                        Text("Compact DB")
                    }
                }
                OutlinedButton(onClick = {
                    val res = IndexRebuilder.rebuildBlocking()
                    Log.w(LOG_TAG, IndexRebuilder.STALL_LOG_MESSAGE)
                    maintenanceStatus = res
                }) {
                    Text("Rebuild index")
                }
                maintenanceStatus?.let { Text(it) }
            }
        }
    }
}

@Composable
fun CheckoutScreen(model: AppModel) {
    val vm = remember { CheckoutViewModel() }
    var quantity by remember { mutableStateOf(vm.quantity) }
    var total by remember { mutableStateOf<String?>(null) }
    var promoCode by remember { mutableStateOf("") }
    var promoStatus by remember { mutableStateOf<String?>(null) }

    ScreenColumn {
        Text("Checkout", style = MaterialTheme.typography.headlineMedium)
        Text("Base price $9.37/unit")
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Text("Quantity")
            OutlinedButton(onClick = {
                vm.setQuantity(vm.quantity - 1)
                quantity = vm.quantity
            }) { Text("−") }
            Text("$quantity", style = MaterialTheme.typography.titleLarge)
            OutlinedButton(onClick = {
                vm.setQuantity(vm.quantity + 1)
                quantity = vm.quantity
            }) { Text("+") }
        }
        Button(onClick = { total = vm.applyDiscount() }) { Text("Apply discount") }
        total?.let { Text("Total: $it", style = MaterialTheme.typography.headlineSmall) }
        OutlinedTextField(
            value = promoCode,
            onValueChange = { promoCode = it },
            label = { Text("Promo code") },
            modifier = Modifier.fillMaxWidth(),
        )
        Button(onClick = { promoStatus = vm.redeemPromo(promoCode) }) { Text("Redeem") }
        promoStatus?.let { Text(it) }
    }
}
