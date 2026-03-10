#!/bin/bash

# --- Configuration ---
API_URL="http://localhost:8083/log"
AUTH_TOKEN="your_secret_token" # ถ้ามี
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# --- Payload ---
# สร้าง JSON สำหรับส่ง (ปรับเปลี่ยนตาม Schema ของคุณ)
PAYLOAD=$(cat <<EOF
{
  "timestamp": "$TIMESTAMP",
  "level": "INFO",
  "service": "auth-service",
  "message": "User login successful",
  "host": "$(hostname)"
}
EOF
)

# --- Send Request ---
echo "Sending log to $API_URL..."

curl -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $AUTH_TOKEN" \
     -d "$PAYLOAD" \
     -v  # -v เพื่อดู Response รายละเอียด (ลบออกได้ถ้าไม่อยากเห็นเยอะ)

echo -e "\nDone."