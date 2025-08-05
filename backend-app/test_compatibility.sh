#!/bin/bash
# Script de prueba para endpoint de compatibilidad
echo ' Probando endpoint de compatibilidad (Fases 1-3)...'

curl -X POST http://localhost:3000/api/issue-credential   -H 'Content-Type: application/json'   -d '{
    " userId:
