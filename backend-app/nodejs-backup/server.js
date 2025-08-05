const express = require('express');
const { initializeAgent } = require('./agent');
const { setupCredentialListener, offerCredential } = require('./credentials');
const { generateQRPage, storeInvitation, getInvitation } = require('./qr-generator');
const { ConnectionEventTypes } = require('@credo-ts/core');

const app = express();
app.use(express.json());

async function main() {
  const agent = await initializeAgent();
  
  // Configurar listeners de eventos
  setupCredentialListener(agent);
  
  // Listener para conexiones entrantes
  agent.events.on(ConnectionEventTypes.ConnectionStateChanged, async ({ payload }) => {
    const connectionRecord = payload.connectionRecord;
    
    if (connectionRecord.state === 'completed') {
      console.log(`🤝 Nueva conexión establecida: ${connectionRecord.id}`);
      
      // Buscar datos de Moodle asociados a esta conexión
      const invitationId = connectionRecord.invitationId;
      const storedData = getInvitation(invitationId);
      
      if (storedData) {
        console.log(`📋 Procesando credencial para: ${storedData.moodleData.userName}`);
        
        // Ofrecer credencial automáticamente
        setTimeout(async () => {
          await offerCredential(agent, connectionRecord.id, storedData.moodleData);
        }, 2000); // Pequeña pausa para estabilizar conexión
      }
    }
  });

  // Endpoint principal: recibe notificación de Moodle
  app.post('/api/issue-credential', async (req, res) => {
    console.log('============================================');
    console.log('🎓 ¡Notificación de curso completado recibida!');
    const moodleData = req.body;
    console.log('📋 Datos del estudiante:', moodleData);

    try {
      console.log('🔗 Generando invitación DIDComm...');
      
      // Crear invitación de conexión
      const { invitation, outOfBandRecord } = await agent.oob.createInvitation({
        label: `Credencial: ${moodleData.courseName}`,
        handshakeProtocols: ['https://didcomm.org/connections/1.0'],
      });
      
      const invitationUrl = invitation.toUrl({ domain: 'http://localhost:3000' });
      
      // Almacenar invitación con datos de Moodle
      const invitationId = storeInvitation(outOfBandRecord.id, moodleData);
      
      // URL para mostrar QR
      const qrPageUrl = `http://localhost:3000/credential-qr/${invitationId}`;
      
      console.log('✅ Invitación generada exitosamente');
      console.log(`🔗 URL del QR: ${qrPageUrl}`);
      console.log('============================================');
      
      res.status(200).json({ 
        success: true,
        qrPageUrl: qrPageUrl,
        message: 'Invitación generada. El estudiante puede escanear el QR para recibir su credencial.'
      });

    } catch (error) {
      console.error('❌ Error generando invitación:', error.message);
      
      // Respuesta de error pero informativa
      res.status(500).json({ 
        success: false,
        message: 'Error generando invitación. Verificar logs del servidor.',
        error: error.message
      });
    }
  });

  // Endpoint para mostrar página con QR
  app.get('/credential-qr/:invitationId', async (req, res) => {
    const invitationId = req.params.invitationId;
    console.log(`📱 Solicitada página QR para invitación: ${invitationId}`);
    
    try {
      const storedData = getInvitation(invitationId);
      
      if (!storedData) {
        return res.status(404).send(`
          <html>
            <body style="font-family: Arial; text-align: center; padding: 2rem;">
              <h1>❌ Invitación no encontrada</h1>
              <p>Esta invitación puede haber expirado o ya fue utilizada.</p>
            </body>
          </html>
        `);
      }
      
      // Generar URL de invitación real
      const invitationUrl = `http://localhost:3000/invitation/${invitationId}`;
      
      // Generar página HTML con QR
      const htmlPage = await generateQRPage(invitationUrl, storedData.moodleData);
      
      res.setHeader('Content-Type', 'text/html');
      res.send(htmlPage);
      
    } catch (error) {
      console.error('❌ Error generando página QR:', error);
      res.status(500).send('Error generando página QR');
    }
  });

  // Endpoint para que las wallets obtengan la invitación
  app.get('/invitation/:invitationId', async (req, res) => {
    const invitationId = req.params.invitationId;
    console.log(`🔗 Wallet solicitando invitación: ${invitationId}`);
    
    try {
      const storedData = getInvitation(invitationId);
      
      if (!storedData) {
        return res.status(404).json({ error: 'Invitación no encontrada' });
      }
      
      // Devolver invitación en formato DIDComm
      res.json(storedData.invitation);
      
    } catch (error) {
      console.error('❌ Error sirviendo invitación:', error);
      res.status(500).json({ error: 'Error procesando invitación' });
    }
  });

  // Endpoint de salud mejorado
  app.get('/health', (req, res) => {
    res.status(200).json({ 
      status: 'OK', 
      message: 'Backend Fase 4 - Credenciales W3C funcionando',
      endpoints: {
        qr: '/credential-qr/:id',
        invitation: '/invitation/:id',
        issue: '/api/issue-credential'
      },
      features: [
        'Credenciales W3C',
        'DIDComm Protocol',
        'QR Code Generation',
        'Fabric Integration'
      ]
    });
  });

  app.listen(3000, '0.0.0.0', () => {
    console.log('🚀 Servidor Fase 4 iniciado en puerto 3000');
    console.log('📋 Funcionalidades activas:');
    console.log('  • Credenciales W3C verificables');
    console.log('  • Protocolo DIDComm');
    console.log('  • Generación de códigos QR');
    console.log('  • Integración con Hyperledger Fabric');
    console.log('  • Compatible con wallets estándar del mercado');
  });
}

main().catch((error) => {
  console.error('💥 Error fatal iniciando servidor:', error);
  process.exit(1);
});