const { CredentialEventTypes } = require('@credo-ts/core');
const crypto = require('crypto');
const { submitToLedger } = require('./fabric-client');
const { DIDManager } = require('./did-manager');

const didManager = new DIDManager();

const setupCredentialListener = (agent) => {
  agent.events.on(CredentialEventTypes.CredentialStateChanged, ({ payload }) => {
    if (payload.credentialRecord.state === 'done') {
      console.log(`✅ Credencial W3C emitida y aceptada por el titular!`);
    }
  });
};

// Crear credencial verificable W3C real
const createW3CCredential = (moodleData) => {
  const universityDID = didManager.getUniversityDID();
  const studentDID = didManager.generateStudentDID(moodleData.userId);
  
  const credentialData = {
    '@context': [
      'https://www.w3.org/2018/credentials/v1',
      'https://www.w3.org/2018/credentials/examples/v1'
    ],
    id: `urn:uuid:${crypto.randomUUID()}`,
    type: ['VerifiableCredential', 'UniversityDegreeCredential'],
    issuer: universityDID,
    issuanceDate: new Date().toISOString(),
    expirationDate: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // 1 año
    credentialSubject: {
      id: studentDID,
      name: moodleData.userName,
      email: moodleData.userEmail,
      degree: {
        type: 'CourseCompletion',
        name: moodleData.courseName,
        completionDate: moodleData.completionDate
      },
      university: {
        name: 'Universidad Ejemplo',
        did: universityDID
      }
    }
  };
  
  // Firmar la credencial
  const proof = didManager.signCredential(credentialData);
  credentialData.proof = proof;
  
  return credentialData;
};

const offerCredential = async (agent, connectionId, moodleData) => {
  console.log(`🎓 Creando credencial W3C para ${moodleData.userName}...`);

  try {
    // Crear credencial W3C real
    const w3cCredential = createW3CCredential(moodleData);
    
    // Registrar en Fabric
    const credentialString = JSON.stringify(w3cCredential);
    const credentialHash = crypto.createHash('sha256').update(credentialString).digest('hex');
    await submitToLedger(moodleData.userId.toString(), moodleData.courseName, credentialHash);
    
    console.log('📝 Hash de credencial W3C registrado en Fabric');
    
    // Preparar atributos para Credo-TS
    const credentialPreview = {
      '@type': 'https://didcomm.org/issue-credential/2.0/credential-preview',
      attributes: [
        { name: 'student_name', value: moodleData.userName },
        { name: 'student_email', value: moodleData.userEmail },
        { name: 'course_name', value: moodleData.courseName },
        { name: 'completion_date', value: moodleData.completionDate },
        { name: 'credential_hash', value: credentialHash },
        { name: 'university', value: 'Universidad Ejemplo' }
      ]
    };

    // Enviar oferta de credencial vía DIDComm
    const credentialExchangeRecord = await agent.credentials.offerCredential({
      connectionId: connectionId,
      protocolVersion: 'v2',
      credentialFormats: {
        jsonld: {
          credential: w3cCredential,
          options: {
            proofType: 'Ed25519Signature2018'
          }
        }
      },
      preview: credentialPreview
    });

    console.log('📱 Oferta de credencial W3C enviada vía DIDComm a la wallet');
    return credentialExchangeRecord;
    
  } catch (error) {
    console.error('❌ Error al ofrecer credencial:', error.message);
    
    // Fallback a credencial simple
    console.log('🔄 Enviando credencial básica como respaldo...');
    
    const basicCredential = await agent.credentials.offerCredential({
      connectionId: connectionId,
      protocolVersion: 'v2',
      credentialFormats: {
        anoncreds: {
          credentialDefinitionId: 'basic-cred-def',
          attributes: [
            { name: 'name', value: moodleData.userName },
            { name: 'course', value: moodleData.courseName },
            { name: 'date', value: moodleData.completionDate }
          ]
        }
      }
    });
    
    return basicCredential;
  }
};

module.exports = { setupCredentialListener, offerCredential };