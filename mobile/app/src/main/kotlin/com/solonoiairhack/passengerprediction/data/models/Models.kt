package com.solonoiairhack.passengerprediction.data.models

data class LoginRequest(
    val email: String,
    val password: String
)

data class LoginResponse(
    val access_token: String,
    val token_type: String,
    val employee_id: String,
    val name: String
)

data class RegisterRequest(
    val employee_id: String,
    val name: String,
    val email: String,
    val password: String,
    val role: String = "employee"
)

data class User(
    val employee_id: String,
    val name: String,
    val email: String,
    val role: String
)

data class Alert(
    val id: String,
    val time_window: String,
    val predicted_load: Int,
    val recommended_desks: Int,
    val threshold_level: Int,
    val status: String,  // OPEN, ACKNOWLEDGED, RESOLVED
    val created_at: String,
    val acknowledged_by: String? = null
)

data class Forecast(
    val time_window: String,
    val predicted_load: Int,
    val recommended_desks: Int
)

data class DashboardStats(
    val passengers_in_system: Int,
    val passengers_in_queue: Int,
    val processed_count: Int,
    val open_desks: Int,
    val next_peak_window: String,
    val alerts: List<Alert>
)

data class FCMTokenRequest(
    val fcm_token: String
)
