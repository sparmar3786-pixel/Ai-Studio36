package com.sparmar.smartsignal

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val Ink = Color(0xFF0B1220)
private val Panel = Color(0xFF151F31)
private val Mint = Color(0xFF43D9A3)
private val Muted = Color(0xFF9BAAC0)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme(colorScheme = darkColorScheme(primary = Mint, background = Ink, surface = Panel)) { Dashboard() } }
    }
}

@Composable
private fun Dashboard() {
    LazyColumn(
        modifier = Modifier.fillMaxSize().background(Ink).padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Text("SMART SIGNAL", color = Mint, fontSize = 13.sp, fontWeight = FontWeight.Bold)
            Text("Market intelligence", color = Color.White, fontSize = 28.sp, fontWeight = FontWeight.Bold)
            Text("Angel One • signal-only terminal", color = Muted, fontSize = 13.sp)
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = Panel), shape = RoundedCornerShape(20.dp)) {
                Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                        Text("LIVE SIGNAL", color = Muted, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        Surface(color = Color(0xFF4A3517), shape = RoundedCornerShape(50)) {
                            Text("WAIT", color = Color(0xFFFFCF78), modifier = Modifier.padding(horizontal = 12.dp, vertical = 5.dp), fontWeight = FontWeight.Bold)
                        }
                    }
                    Text("Data required", color = Color.White, fontSize = 24.sp, fontWeight = FontWeight.Bold)
                    Text("No BUY/SELL until live data freshness and strategy checks pass.", color = Muted)
                    HorizontalDivider(color = Color(0xFF29364B))
                    SignalRow("Entry", "—")
                    SignalRow("Stop-loss", "—")
                    SignalRow("Targets", "T1 —  •  T2 —  •  T3 —")
                    SignalRow("Strike", "—")
                }
            }
        }
        item {
            Text("CONFLUENCE ENGINE", color = Mint, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            Card(colors = CardDefaults.cardColors(containerColor = Panel), shape = RoundedCornerShape(18.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    SignalRow("Open interest", "Waiting for verified feed")
                    SignalRow("OI state", "Neutral")
                    SignalRow("VWAP / EMA trend", "Unavailable")
                    SignalRow("PCR / option chain", "Unavailable")
                    SignalRow("Data freshness", "NOT CONNECTED")
                }
            }
        }
        item {
            Text("RISK GUARD", color = Mint, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            Card(colors = CardDefaults.cardColors(containerColor = Panel), shape = RoundedCornerShape(18.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Paper / signal-only mode", color = Color.White, fontWeight = FontWeight.SemiBold)
                    Text("No broker orders are sent. Stale or missing data blocks signals. Stops and targets are estimates, not guaranteed exits.", color = Muted)
                }
            }
        }
        item { Text("No strategy can guarantee 15% daily profit. Validate with paper trading before risking capital.", color = Muted, fontSize = 12.sp) }
    }
}

@Composable
private fun SignalRow(label: String, value: String) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
        Text(label, color = Muted, fontSize = 13.sp)
        Text(value, color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
    }
}
