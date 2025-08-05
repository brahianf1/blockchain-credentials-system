const QRCode = require('qrcode');
const crypto = require('crypto');

// Almacén temporal de invitaciones (en producción sería Redis/DB)
const pendingInvitations = new Map();

const generateQRPage = async (invitationUrl, moodleData) => {
  try {
    // Generar QR code como Data URL
    const qrCodeDataUrl = await QRCode.toDataURL(invitationUrl, {
      width: 300,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#FFFFFF'
      }
    });

    // Crear página HTML con QR
    const html = `
      <!DOCTYPE html>
      <html lang="es">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Recibir Credencial - Universidad Ejemplo</title>
          <style>
            body {
              font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
              display: flex;
              justify-content: center;
              align-items: center;
              min-height: 100vh;
              margin: 0;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: #333;
            }
            .container {
              background: white;
              padding: 2rem;
              border-radius: 15px;
              box-shadow: 0 10px 30px rgba(0,0,0,0.2);
              text-align: center;
              max-width: 400px;
            }
            h1 {
              color: #2c3e50;
              margin-bottom: 0.5rem;
            }
            .course-name {
              color: #3498db;
              font-weight: bold;
              font-size: 1.2em;
              margin: 1rem 0;
            }
            .instructions {
              color: #666;
              margin: 1rem 0;
              line-height: 1.6;
            }
            .qr-container {
              margin: 1.5rem 0;
              padding: 1rem;
              background: #f8f9fa;
              border-radius: 10px;
            }
            .qr-code {
              border: 3px solid #fff;
              border-radius: 10px;
              box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            .wallet-info {
              background: #e8f5e8;
              padding: 1rem;
              border-radius: 8px;
              margin-top: 1rem;
              font-size: 0.9em;
              color: #2d5a3d;
            }
            .footer {
              margin-top: 2rem;
              font-size: 0.8em;
              color: #999;
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>🎓 ¡Felicidades, ${moodleData.userName}!</h1>
            
            <div class="course-name">
              "${moodleData.courseName}"
            </div>
            
            <div class="instructions">
              Has completado exitosamente tu curso. Escanea el código QR con tu wallet de identidad para recibir tu credencial verificable.
            </div>
            
            <div class="qr-container">
              <img src="${qrCodeDataUrl}" alt="Código QR para credencial" class="qr-code" />
            </div>
            
            <div class="wallet-info">
              <strong>📱 Wallets recomendadas:</strong><br>
              • Lissi Wallet<br>
              • Trinsic Wallet<br>
              • Esatus Wallet
            </div>
            
            <div class="footer">
              Universidad Ejemplo - Sistema de Credenciales Verificables
            </div>
          </div>
        </body>
      </html>
    `;

    return html;
    
  } catch (error) {
    console.error('Error generando página QR:', error);
    throw error;
  }
};

const storeInvitation = (invitationData, moodleData) => {
  const invitationId = crypto.randomBytes(16).toString('hex');
  pendingInvitations.set(invitationId, {
    invitation: invitationData,
    moodleData: moodleData,
    createdAt: Date.now()
  });
  
  // Limpiar invitaciones viejas (más de 1 hora)
  setTimeout(() => {
    pendingInvitations.delete(invitationId);
  }, 3600000);
  
  return invitationId;
};

const getInvitation = (invitationId) => {
  return pendingInvitations.get(invitationId);
};

module.exports = {
  generateQRPage,
  storeInvitation,
  getInvitation
};
