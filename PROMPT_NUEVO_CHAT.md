# PROMPT PARA NUEVO CHAT - FASE 4 BLOCKCHAIN MVP

## CONTEXTO PRINCIPAL
Tengo un MVP de blockchain con 4 fases funcionales. **La Fase 4 implementa credenciales W3C reales con DIDComm** pero está fallando en la inicialización del agente Credo-TS v0.5.x. El objetivo crítico es **"pasar de lo simulado a lo real"** - hacer que funcione en modo producción real, no simulación.

**IMPORTANTE**: Lee primero las guías del proyecto para entender el contexto completo:
- `GUIA_FASE_1_HIBRIDA.md` - Configuración inicial Hyperledger Fabric 
- `GUIA_FASE_2_HIBRIDA.md` - Integración con Moodle LMS
- `GUIA_FASE_3_HIBRIDA.md` - Backend Node.js y APIs
- `GUIA_FASE_4_HIBRIDA.md` - Credenciales W3C con DIDComm (PROBLEMA ACTUAL)

El proyecto completo busca crear un sistema de certificación académica descentralizada usando blockchain.

## ESTADO ACTUAL DEL SISTEMA
- **Hyperledger Fabric**: v2.5.12 funcionando correctamente
- **Moodle**: v4.3.5 LMS operativo  
- **Backend Node.js**: Express server con problema en agente DIDComm
- **Docker**: WSL2 Ubuntu 22.04 con edición híbrida Windows

## PROBLEMA ESPECÍFICO
El agente Credo-TS v0.5.x falla consistentemente con error:
```
Error opening wallet universidad-wallet-real-v5: Cannot read properties of undefined (reading 'storeOpen')
```

**NOTA CRÍTICA**: Si el problema persiste con v0.5.x, considera evaluar si hay versiones más estables de Credo-TS que funcionen mejor. La v0.5.x podría tener issues de migración que hagan más viable usar otra versión.

**ANÁLISIS REQUERIDO**: Investiga también si el problema es arquitectural - puede que falten:
- Servicios adicionales para modo producción
- Configuraciones específicas para entorno real vs simulado  
- Dependencias o módulos complementarios
- Archivos de configuración de infraestructura

## INVESTIGACIÓN REALIZADA
1. **Arquitectura v0.5.x**: Credo migró de wallet config legacy a AskarModule pero con validación inconsistente
2. **Configuraciones probadas**: 
   - `ariesAskar: askar` vs `askar: askar`  
   - Múltiples configuraciones de store
   - Walletconfig híbridos para validación legacy
3. **Root cause**: AskarModule no está recibiendo correctamente la instancia de askar

## ARCHIVOS CRÍTICOS

**agent.js** (problema principal):
```javascript
const { AskarModule } = require('@credo-ts/askar');
const { askar } = require('@openwallet-foundation/askar-nodejs');

// CONFIGURACIÓN ACTUAL QUE FALLA:
const modules = {
  askar: new AskarModule({
    ariesAskar: askar,  // storeOpen undefined
  }),
  // ... otros módulos
};
```

**package.json** (dependencias actuales):
```json
{
  "dependencies": {
    "@credo-ts/core": "^0.5.12",
    "@credo-ts/askar": "^0.5.12", 
    "@openwallet-foundation/askar-nodejs": "^0.2.3"
  }
}
```

## CONFIGURACIONES OFICIALES ENCONTRADAS
En la investigación GitHub se encontraron estos patrones oficiales v0.5.x:

**Demo oficial**:
```javascript
askar: new AskarModule({
  askar,  // NO ariesAskar
  store: askarStoreConfig,
})
```

**Test helpers**:
```javascript
askar: new AskarModule({
  askar,
  store: {
    id: `SQLiteWallet${name}`,
    key: `Key${name}`,
    database: { type: 'sqlite', config: { inMemory } },
  },
})
```

## PRÓXIMO PASO CRÍTICO
**ENFOQUE ABIERTO**: No te limites a solo corregir la configuración actual. Evalúa:

1. **Si v0.5.x es la mejor opción** - Puede que haya versiones más maduras/estables
2. **Arquitectura completa** - ¿Falta algún componente para modo producción?
3. **Configuración AskarModule** - Según patrones oficiales encontrados
4. **Dependencias faltantes** - ¿Hay paquetes adicionales para modo real?
5. **Alternativas de implementación** - Si la versión actual tiene problemas arquitecturales

**METODOLOGÍA**: Siempre consulta fuentes oficiales, documentación técnica y foros especializados antes de implementar.

**PRIORIDAD**: Lograr que funcione en modo REAL, no importa si requiere cambiar versión de Credo-TS o arquitectura.

## COMANDO PARA PROBAR
```bash
cd c:\Users\flore\Documents\blockchain\backend-app
docker compose up --build -d
docker compose logs backend-app
```

## OBJETIVO FINAL
Que aparezca en logs:
```
✅ ¡ÉXITO! Agente Credo v0.5.x inicializado en modo REAL
🎯 Sistema funcionando en modo PRODUCCIÓN - NO simulación
```

## ESTRUCTURA WORKSPACE
```
c:\Users\flore\Documents\blockchain\
├── backend-app/
│   ├── agent.js          # ← ARCHIVO PROBLEMA
│   ├── package.json      # ← Dependencias OK
│   ├── server.js         # ← Server principal
│   └── docker-compose.yml
└── fabric-samples/       # ← Fabric funcionando
```

## CONTEXTO DE URGENCIA
- **Usuario enfatizó**: "la prioridad ahora en esta Fase 4"
- **Objetivo clave**: Transición exitosa de simulación a modo real
- **Estado**: Problema persistente con v0.5.x, puede requerir cambio de versión

**INSTRUCCIÓN**: 
1. **Primero**: Lee las guías del proyecto para entender el contexto completo
2. **Segundo**: Haz un análisis arquitectural completo - evalúa si falta algo a nivel:
   - **Dependencias**: ¿Hay paquetes faltantes para modo producción?
   - **Configuración**: ¿Faltan archivos de config específicos para real vs simulado?
   - **Arquitectura**: ¿El diseño actual soporta modo producción real?
   - **Servicios**: ¿Hay servicios externos o internos que deben estar corriendo?
3. **Tercero**: BUSCA en fuentes oficiales y expertas:
   - **Documentación oficial** de Credo-TS y OpenWallet Foundation
   - **StackOverflow** para problemas similares con DIDComm/Askar
   - **GitHub Issues** del repositorio oficial
   - **Foros de desarrolladores** especializados en identidad digital
4. **Cuarto**: Evalúa si v0.5.x es viable o si hay mejores versiones de Credo-TS
5. **Quinto**: Implementa la solución más estable para lograr modo REAL (no simulación)
