"""Firebase Cloud Messaging service for sending push notifications to mobile employees."""

import os
import firebase_admin
from firebase_admin import credentials, messaging
from src.auth.auth import get_all_fcm_tokens

# Initialize Firebase (requires google-services.json in the project root or env setup)
FIREBASE_CREDS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-service-account.json")

try:
    if os.path.exists(FIREBASE_CREDS_PATH):
        cred = credentials.Certificate(FIREBASE_CREDS_PATH)
        firebase_admin.initialize_app(cred)
        FIREBASE_ENABLED = True
    else:
        FIREBASE_ENABLED = False
        print(f"Warning: Firebase credentials not found at {FIREBASE_CREDS_PATH}. Push notifications disabled.")
except Exception as e:
    FIREBASE_ENABLED = False
    print(f"Warning: Firebase initialization failed: {e}. Push notifications disabled.")


def send_alert_notification(
    alert_id: str,
    predicted_load: int,
    recommended_desks: int,
    threshold_level: int,
    time_window: str
) -> bool:
    """Send push notification to all registered employees about an alert."""
    
    if not FIREBASE_ENABLED:
        print("Firebase not enabled. Skipping push notification.")
        return False
    
    try:
        tokens = get_all_fcm_tokens()
        if not tokens:
            print("No registered FCM tokens found.")
            return False
        
        # Prepare notification
        title = f"Level {threshold_level} Alert"
        if threshold_level == 1:
            body = f"Moderate passenger load. Open 1 extra desk for {time_window}"
        elif threshold_level == 2:
            body = f"High passenger load. Open 2 extra desks for {time_window}"
        else:
            body = f"CRITICAL: Open 4 extra desks for {time_window}!"
        
        # Send to all registered tokens
        for token_info in tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                    ),
                    data={
                        "alert_id": alert_id,
                        "predicted_load": str(predicted_load),
                        "recommended_desks": str(recommended_desks),
                        "threshold_level": str(threshold_level),
                        "time_window": time_window,
                    },
                    token=token_info["fcm_token"],
                )
                
                response = messaging.send(message)
                print(f"Notification sent to {token_info['name']}: {response}")
                
            except Exception as e:
                print(f"Failed to send notification to {token_info['employee_id']}: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error sending push notifications: {e}")
        return False


def send_test_notification(employee_email: str) -> bool:
    """Send a test notification to verify setup."""
    
    if not FIREBASE_ENABLED:
        print("Firebase not enabled. Cannot send test notification.")
        return False
    
    try:
        # For testing, send to all devices
        tokens = get_all_fcm_tokens()
        if not tokens:
            print("No registered devices.")
            return False
        
        message = messaging.Message(
            notification=messaging.Notification(
                title="Test Notification",
                body="This is a test push notification from Passenger Flow Predictor",
            ),
            data={
                "test": "true",
            },
            token=tokens[0]["fcm_token"],
        )
        
        response = messaging.send(message)
        print(f"Test notification sent: {response}")
        return True
        
    except Exception as e:
        print(f"Error sending test notification: {e}")
        return False
