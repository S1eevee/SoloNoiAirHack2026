package com.solonoiairhack.passengerprediction.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.solonoiairhack.passengerprediction.data.models.Alert

@Composable
fun DashboardScreen(navController: NavHostController) {
    var alerts by remember { mutableStateOf(listOf<Alert>()) }
    var passengersInSystem by remember { mutableStateOf(0) }
    var passengersInQueue by remember { mutableStateOf(0) }
    var processedCount by remember { mutableStateOf(0) }
    var openDesks by remember { mutableStateOf(10) }
    var isRefreshing by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        // TODO: Fetch dashboard data from API
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Dashboard") },
                actions = {
                    IconButton(
                        onClick = { /* TODO: Logout */ }
                    ) {
                        Text("Logout")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
        ) {
            // Stats Cards
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                StatCard(
                    label = "Passengers",
                    value = passengersInSystem.toString(),
                    modifier = Modifier.weight(1f)
                )
                StatCard(
                    label = "Queue",
                    value = passengersInQueue.toString(),
                    modifier = Modifier.weight(1f)
                )
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                StatCard(
                    label = "Processed",
                    value = processedCount.toString(),
                    modifier = Modifier.weight(1f)
                )
                StatCard(
                    label = "Open Desks",
                    value = "$openDesks/20",
                    modifier = Modifier.weight(1f)
                )
            }

            // Alerts Section
            Text(
                text = "Active Alerts",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(bottom = 12.dp)
            )

            if (alerts.isEmpty()) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 16.dp)
                ) {
                    Text(
                        text = "No active alerts",
                        modifier = Modifier.padding(16.dp),
                        color = Color.Gray
                    )
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(alerts) { alert ->
                        AlertCard(alert) {
                            // TODO: Acknowledge alert
                        }
                    }
                }
            }

            // Action Buttons
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = { navController.navigate("predictor") },
                    modifier = Modifier
                        .weight(1f)
                        .height(50.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary)
                ) {
                    Text("Passenger Flow Predictor")
                }
                
                Button(
                    onClick = { isRefreshing = true },
                    modifier = Modifier
                        .weight(1f)
                        .height(50.dp)
                ) {
                    Text("Refresh")
                }
            }
        }
    }
}

@Composable
fun StatCard(label: String, value: String, modifier: Modifier = Modifier) {
    Card(modifier = modifier) {
        Column(
            modifier = Modifier.padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(label, style = MaterialTheme.typography.labelSmall, color = Color.Gray)
            Text(value, style = MaterialTheme.typography.headlineSmall)
        }
    }
}

@Composable
fun AlertCard(alert: Alert, onAcknowledge: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = alert.time_window,
                        style = MaterialTheme.typography.titleSmall
                    )
                    Text(
                        text = "${alert.predicted_load} passengers predicted",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color.Gray
                    )
                }
                Text(
                    text = "Level ${alert.threshold_level}",
                    style = MaterialTheme.typography.labelMedium,
                    color = when (alert.threshold_level) {
                        1 -> Color(0xFFFFA500)
                        2 -> Color(0xFFFF6B6B)
                        else -> Color(0xFF8B0000)
                    }
                )
            }

            Text(
                text = "Open ${alert.recommended_desks} desks",
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(bottom = 8.dp)
            )

            if (alert.status == "OPEN") {
                Button(
                    onClick = onAcknowledge,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Acknowledge")
                }
            } else {
                Text(
                    text = "Status: ${alert.status}",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.Green
                )
            }
        }
    }
}

@Composable
fun IconButton(onClick: () -> Unit, content: @Composable () -> Unit) {
    Button(onClick = onClick) {
        content()
    }
}
