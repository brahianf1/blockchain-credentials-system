#!/bin/bash
# Comando de prueba simplificado
echo "🧪 Probando endpoint de credenciales..."

curl -X POST http://localhost:3000/api/credential/request \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "123",
    "student_name": "Juan Pérez",
    "student_email": "estudiante@ejemplo.com",
    "course_id": "curso-001",
    "course_name": "Introducción a Blockchain",
    "completion_date": "2025-08-03T10:30:00Z",
    "grade": "A",
    "instructor_name": "Prof. García"
  }' | jq .

echo ""
echo "✅ Prueba completada. Copiar el connection_id de arriba para ver el QR."
echo "📱 Abrir: http://localhost:3000/qr/[CONNECTION_ID]"
