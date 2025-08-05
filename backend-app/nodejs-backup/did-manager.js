const crypto = require('crypto');

// Gestor simple de DIDs para la universidad
class DIDManager {
  constructor() {
    // En producción esto vendría de una base de datos segura
    this.universityDID = 'did:web:universidad-ejemplo.com:issuer';
    this.universityKeys = this.generateKeyPair();
  }
  
  generateKeyPair() {
    // Generar par de claves Ed25519 para firmado
    const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519', {
      publicKeyEncoding: { type: 'spki', format: 'pem' },
      privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
    });
    
    return { publicKey, privateKey };
  }
  
  getUniversityDID() {
    return this.universityDID;
  }
  
  signCredential(credentialData) {
    // Crear firma digital de la credencial
    const sign = crypto.createSign('Ed25519');
    sign.update(JSON.stringify(credentialData));
    const signature = sign.sign(this.universityKeys.privateKey, 'base64');
    
    return {
      type: 'Ed25519Signature2018',
      created: new Date().toISOString(),
      verificationMethod: `${this.universityDID}#key-1`,
      proofValue: signature
    };
  }
  
  // Generar DID para estudiante (simplificado para MVP)
  generateStudentDID(userId) {
    return `did:local:student:${userId}`;
  }
}

module.exports = { DIDManager };
