#!/usr/bin/env python3
import requests
import json

# Datos de prueba
data = {
    "student_id": "123",
    "student_name": "Juan Pérez", 
    "student_email": "estudiante@ejemplo.com",
    "course_id": "curso-001",
    "course_name": "Introducción a Blockchain",
    "completion_date": "2025-08-03T10:30:00Z",
    "grade": "A",
    "instructor_name": "Prof. García"
}

print("🧪 Probando endpoint...")
print(f"Datos: {json.dumps(data, indent=2)}")

try:
    response = requests.post(
        "http://localhost:3000/api/credential/request",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"✅ Status Code: {response.status_code}")
    print(f"📝 Response Headers: {dict(response.headers)}")
    print(f"📄 Response Body: {response.text}")
    
    if response.status_code == 200:
        response_data = response.json()
        print(f"🎯 Success: {response_data}")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"💥 Exception: {e}")
