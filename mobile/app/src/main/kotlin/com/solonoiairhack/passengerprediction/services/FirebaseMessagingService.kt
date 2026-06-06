package com.solonoiairhack.passengerprediction.services

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.solonoiairhack.passengerprediction.MainActivity
import com.solonoiairhack.passengerprediction.R

class MyFirebaseMessagingService : FirebaseMessagingService() {

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        // Handle push notification
        val title = remoteMessage.notification?.title ?: "Passenger Flow Alert"
        val body = remoteMessage.notification?.body ?: "Check your dashboard"
        val load = remoteMessage.data["predicted_load"] ?: "Unknown"
        val recommendedDesks = remoteMessage.data["recommended_desks"] ?: "Unknown"

        val message = "$body\nLoad: $load passengers | Desks needed: $recommendedDesks"
        sendNotification(title, message)
    }

    override fun onNewToken(token: String) {
        // Send token to backend (handled by app when user logs in)
    }

    private fun sendNotification(title: String, body: String) {
        val intent = Intent(this, MainActivity::class.java)
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE
        )

        val notificationId = 1001
        val channelId = "passenger_alerts"

        val notificationBuilder = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_HIGH)

        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Passenger Flow Alerts",
                NotificationManager.IMPORTANCE_HIGH
            )
            manager.createNotificationChannel(channel)
        }

        manager.notify(notificationId, notificationBuilder.build())
    }
}
