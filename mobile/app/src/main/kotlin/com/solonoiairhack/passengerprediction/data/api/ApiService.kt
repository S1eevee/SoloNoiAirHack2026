package com.solonoiairhack.passengerprediction.data.api

import retrofit2.http.*
import com.solonoiairhack.passengerprediction.data.models.*

interface PassengerPredictionApi {
    
    // Auth endpoints
    @POST("/auth/register")
    suspend fun register(@Body request: RegisterRequest): Map<String, String>
    
    @POST("/auth/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse
    
    @POST("/auth/fcm-token")
    suspend fun saveFcmToken(
        @Header("Authorization") token: String,
        @Body request: FCMTokenRequest
    ): Map<String, String>
    
    @GET("/auth/me")
    suspend fun getCurrentUser(
        @Header("Authorization") token: String
    ): User
    
    // Dashboard endpoints
    @GET("/alerts")
    suspend fun getAlerts(
        @Header("Authorization") token: String,
        @Query("status") status: String? = null
    ): List<Alert>
    
    @POST("/alerts/{id}/acknowledge")
    suspend fun acknowledgeAlert(
        @Header("Authorization") token: String,
        @Path("id") alertId: String,
        @Body body: Map<String, String>
    ): Map<String, String>
    
    @GET("/forecast")
    suspend fun getForecast(
        @Header("Authorization") token: String
    ): List<Forecast>
}
