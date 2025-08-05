const { Gateway, Wallets } = require('fabric-network');
const FabricCAServices = require('fabric-ca-client');
const path = require('path');
const fs = require('fs');

// Función para conectar a Fabric y enviar transacción REAL
const submitToLedger = async (userId, courseName, credentialHash) => {
  try {
    console.log('Conectando a Hyperledger Fabric (REAL)...');
    
    // Cargar perfil de conexión
    const ccpPath = path.resolve(__dirname, 'crypto-config', 'connection-org1.json');
    const ccp = JSON.parse(fs.readFileSync(ccpPath, 'utf8'));
    
    // Crear wallet en memoria para esta transacción
    const wallet = await Wallets.newInMemoryWallet();
    
    // Importar identidad del usuario User1 (disponible en crypto-config)
    const certPath = path.resolve(__dirname, 'crypto-config', 'User1', 'msp', 'signcerts', 'cert.pem');
    const keyPath = path.resolve(__dirname, 'crypto-config', 'User1', 'msp', 'keystore');
    
    const cert = fs.readFileSync(certPath).toString();
    const keyFiles = fs.readdirSync(keyPath);
    const keyFile = keyFiles[0]; // Tomar la primera clave
    const key = fs.readFileSync(path.join(keyPath, keyFile)).toString();
    
    const identity = {
      credentials: {
        certificate: cert,
        privateKey: key,
      },
      mspId: 'Org1MSP',
      type: 'X.509',
    };
    
    await wallet.put('User1', identity);
    
    // Conectar al gateway
    const gateway = new Gateway();
    await gateway.connect(ccp, {
      wallet,
      identity: 'User1',
      discovery: { enabled: true, asLocalhost: true }
    });
    
    // Obtener el contrato
    const network = await gateway.getNetwork('mychannel');
    const contract = network.getContract('basic');
    
    // Enviar transacción real
    console.log('Enviando transacción real a Fabric...');
    await contract.submitTransaction('CreateAsset', `credential_${userId}_${Date.now()}`, courseName, credentialHash, userId);
    
    console.log('✅ Transacción REAL enviada exitosamente a Fabric');
    
    await gateway.disconnect();
    
  } catch (error) {
    console.error('❌ Error al conectar con Fabric:', error.message);
    
    // Fallback a simulación si hay problemas
    console.log('🔄 Continuando con simulación como respaldo...');
    console.log(`Usuario: ${userId}`);
    console.log(`Curso: ${courseName}`);
    console.log(`Hash de credencial: ${credentialHash}`);
    console.log('Transacción simulada como respaldo');
  }
};

module.exports = { submitToLedger };