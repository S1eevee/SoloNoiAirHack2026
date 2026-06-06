# Mobile App — Android Employee Dashboard

A **Kotlin/Android native app** for airport employees to:
- **Register & login** with their employee ID
- **Receive push notifications** when more check-in desks need to be opened
- **View real-time dashboard** with passenger flow stats
- **Acknowledge alerts** directly from their phone

---

## Setup

### 1. Prerequisites

- Android Studio (latest)
- Android SDK 24+ 
- Firebase project set up (https://console.firebase.google.com)

### 2. Get Firebase Credentials

1. Create a project in [Firebase Console](https://console.firebase.google.com)
2. Add Android app with package name: `com.solonoiairhack.passengerprediction`
3. Download `google-services.json` and place in `mobile/app/`

### 3. Build & Run

```bash
cd mobile
./gradlew build
# Then open in Android Studio and run on emulator or device
```

### 4. Update Backend URL

Edit `mobile/app/src/main/kotlin/com/solonoiairhack/passengerprediction/data/api/RetrofitClient.kt`:

```kotlin
private const val BASE_URL = "http://YOUR_API_SERVER:8000/"
```

---

## Architecture

```
Screens:
├── LoginScreen      → /auth/login
├── RegisterScreen   → /auth/register
└── DashboardScreen  → /alerts, /forecast

Services:
├── FirebaseMessagingService    → Handles push notifications
└── ApiService                  → Retrofit API client

Models:
├── LoginRequest/Response
├── Alert
├── Forecast
└── DashboardStats

Data:
└── SharedPreferences (store JWT token)
```

---

## API Integration

### Authentication Flow

1. **Register** → `POST /auth/register`
2. **Login** → `POST /auth/login` → Get JWT token
3. **Save FCM Token** → `POST /auth/fcm-token` (for push notifications)
4. **Fetch Alerts** → `GET /alerts?status=OPEN` (with JWT token)

### Push Notifications

1. Backend generates alert
2. Backend sends Firebase Cloud Message to employee's FCM token
3. `FirebaseMessagingService.onMessageReceived()` is triggered
4. Notification appears on employee's home screen
5. Tapping notification opens app → Dashboard

### FCM Token Registration

After successful login, the app registers the device:

```kotlin
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        // Send token to backend
        apiService.saveFcmToken("Bearer $jwtToken", FCMTokenRequest(token))
    }
}
```

---

## Features

### Implemented
- Login/Register screens
- JWT token management
- API client setup
- Firebase messaging service
- Dashboard with stats
- Alert acknowledgement UI

### TODO (Next Phase)
- Connect login/register to actual API
- Implement API calls for dashboard data
- Real-time updates via polling or WebSocket
- Push notification testing
- Employee profile settings
- Offline queue for actions

---

## Push Notification Flow

```
XGBoost Prediction → Alert Generated
           ↓
API sends Firebase message:
{
  "title": "High Load Alert",
  "body": "Check-in flow increasing",
  "data": {
    "predicted_load": "450",
    "recommended_desks": "12"
  }
}
           ↓
Employee's Phone receives notification
           ↓
FirebaseMessagingService.onMessageReceived()
           ↓
Show notification + open Dashboard on tap
```

---

## Testing

### Local Testing
1. Start backend API (port 8000)
2. Update API URL to your machine's IP (not localhost)
3. Run emulator or connect device
4. Register test account
5. Check Firebase Console → Cloud Messaging → Send test message

### Push Notification Test
```bash
# From backend console
python3 pipeline.py insights --question "What's next week's peak time?"
# This triggers alerts → sends push notifications to all registered devices
```

---

## Dependencies

| Library | Purpose |
|---------|---------|
| Jetpack Compose | Modern UI framework |
| Retrofit2 | HTTP client for API |
| Firebase Messaging | Push notifications |
| DataStore | Local preferences |
| Navigation Compose | Screen navigation |
| Material3 | Design system |

---

## Folder Structure

```
mobile/
├── app/
│   ├── build.gradle
│   ├── google-services.json          ← Add from Firebase
│   └── src/main/
│       ├── kotlin/
│       │   └── com/solonoiairhack/passengerprediction/
│       │       ├── MainActivity.kt
│       │       ├── data/
│       │       │   ├── api/ApiService.kt
│       │       │   └── models/Models.kt
│       │       ├── services/
│       │       │   └── FirebaseMessagingService.kt
│       │       └── ui/
│       │           ├── screens/
│       │           │   ├── LoginScreen.kt
│       │           │   ├── RegisterScreen.kt
│       │           │   ├── DashboardScreen.kt
│       │           │   └── Navigation.kt
│       │           └── theme/
│       │               └── Theme.kt
│       └── AndroidManifest.xml
├── build.gradle
└── settings.gradle
```
