/**
 * Atlas Vivo MILK - Integração com ORCID API
 * 
 * @description: Script para validar ORCIDs, vincular obras e atualizar perfis no ORCID.
 * @author: Nuno Filipe Fernandes Vieira Cabral e Araújo (ORCID: 0009-0009-1781-4020)
 * @author: Eduardo Maurício Vieira Cabral e Araújo (ORCID: 0009-0007-6892-6570)
 * @license: EUPL-1.2
 * @version: 1.0.0
 * @date: 2026-06-25
 * 
 * @depends: 
 *   - node-fetch (para requisições HTTP)
 *   - dotenv (para variáveis de ambiente)
 * 
 * @usage: 
 *   node orcid_api_integration.js --validate 0009-0009-1781-4020
 *   node orcid_api_integration.js --link 0009-0009-1781-4020 10.5281/zenodo.XXXXXXX
 */

const fetch = require('node-fetch');
const dotenv = require('dotenv');

// Carregar variáveis de ambiente (ORCID_CLIENT_ID, ORCID_CLIENT_SECRET)
dotenv.config();

// Configuração da ORCID API
const ORCID_API_URL = 'https://api.orcid.org/v3.0';
const ORCID_PUBLIC_API_URL = 'https://pub.orcid.org/v3.0';
const ORCID_CLIENT_ID = process.env.ORCID_CLIENT_ID;
const ORCID_CLIENT_SECRET = process.env.ORCID_CLIENT_SECRET;
const ORCID_REDIRECT_URI = process.env.ORCID_REDIRECT_URI || 'https://github.com/milkivc/atlas-datasets';

// Verificar se as credenciais estão configuradas
if (!ORCID_CLIENT_ID || !ORCID_CLIENT_SECRET) {
  console.warn('⚠️ Aviso: ORCID_CLIENT_ID ou ORCID_CLIENT_SECRET não estão configurados. Use variáveis de ambiente.');
}

// Tokens de acesso (a serem obtidos via OAuth2)
let ORCID_ACCESS_TOKEN = null;

/**
 * Função para obter token de acesso via OAuth2
 * @returns {Promise<string>} - Token de acesso
 */
async function getAccessToken() {
  try {
    const authString = Buffer.from(`${ORCID_CLIENT_ID}:${ORCID_CLIENT_SECRET}`).toString('base64');
    
    const response = await fetch('https://orcid.org/oauth/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${authString}`
      },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        scope: '/read-public /activities/update /person/update'
      })
    });

    if (!response.ok) {
      throw new Error(`Erro ao obter token: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    ORCID_ACCESS_TOKEN = data.access_token;
    console.log('✅ Token de acesso obtido com sucesso!');
    return data.access_token;
  } catch (error) {
    console.error('❌ Erro ao obter token:', error.message);
    throw error;
  }
}

/**
 * Função para validar um ORCID
 * @param {string} orcid - ORCID a validar (ex: 0009-0009-1781-4020)
 * @returns {Promise<Object>} - Objeto com os dados do ORCID
 */
async function validateORCID(orcid) {
  try {
    // Normalizar ORCID (remover hífens e converter para minúsculas)
    const normalizedOrcid = orcid.replace(/-/g, '').toLowerCase();
    
    // Verificar formato (deve ter 16 dígitos)
    if (!/^[0-9]{16}$/.test(normalizedOrcid)) {
      throw new Error(`ORCID inválido: ${orcid}. Deve ter 16 dígitos (ex: 0000-0000-0000-0000).`);
    }

    // Consultar API pública do ORCID
    const response = await fetch(`${ORCID_PUBLIC_API_URL}/${normalizedOrcid}/record`, {
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`ORCID não encontrado: ${orcid}`);
      }
      throw new Error(`Erro ao validar ORCID: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ ORCID válido!');
    console.log(`- Nome: ${data.person.name['given-names']?.value || ''} ${data.person.name['family-name']?.value || ''}`);
    console.log(`- ORCID: ${data.person['orcid-identifier'].path}`);
    
    return {
      valid: true,
      orcid: data.person['orcid-identifier'].path,
      name: {
        given: data.person.name['given-names']?.value || '',
        family: data.person.name['family-name']?.value || ''
      },
      bio: data.person.biography?.value || '',
      emails: data.person.emails?.email?.map(email => email.value) || [],
      externalIds: data.person['external-identifiers']?.['external-identifier'] || []
    };
  } catch (error) {
    console.error('❌ Erro ao validar ORCID:', error.message);
    return {
      valid: false,
      orcid: orcid,
      error: error.message
    };
  }
}

/**
 * Função para obter obras vinculadas a um ORCID
 * @param {string} orcid - ORCID do autor
 * @returns {Promise<Array>} - Lista de obras
 */
async function getWorksByORCID(orcid) {
  try {
    const normalizedOrcid = orcid.replace(/-/g, '').toLowerCase();
    
    const response = await fetch(`${ORCID_PUBLIC_API_URL}/${normalizedOrcid}/works`, {
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Erro ao obter obras: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    const works = data.group || [];
    
    console.log(`✅ ${works.length} obras encontradas para ORCID ${orcid}:`);
    works.forEach((group, index) => {
      const work = group['work-summary'][0];
      console.log(`  ${index + 1}. ${work.title?.title?.value || 'Sem título'} (${work['published-in'] || 'Sem data'})`);
      console.log(`     DOI: ${work['doi-data']?.doi || 'N/A'}`);
      console.log(`     URL: ${work.url?.value || 'N/A'}`);
    });
    
    return works.map(group => group['work-summary'][0]);
  } catch (error) {
    console.error('❌ Erro ao obter obras:', error.message);
    return [];
  }
}

/**
 * Função para vincular uma obra (DOI) a um ORCID
 * @param {string} orcid - ORCID do autor
 * @param {string} doi - DOI da obra
 * @param {Object} workData - Dados da obra (título, tipo, etc.)
 * @returns {Promise<Object>} - Resultado da operação
 */
async function linkWorkToORCID(orcid, doi, workData = {}) {
  try {
    // Obter token de acesso
    if (!ORCID_ACCESS_TOKEN) {
      await getAccessToken();
    }

    const normalizedOrcid = orcid.replace(/-/g, '').toLowerCase();
    
    // Dados padrão da obra
    const defaultWorkData = {
      title: {
        title: workData.title || 'Atlas Vivo MILK - Dados de Património Cultural Imaterial'
      },
      type: workData.type || 'dataset',
      url: workData.url || `https://doi.org/${doi}`,
      'external-ids': {
        'external-id': [
          {
            'external-id-type': 'doi',
            'external-id-value': doi,
            'external-id-url': {
              value: `https://doi.org/${doi}`
            },
            'external-id-relationship': 'SELF'
          }
        ]
      },
      'published-in': workData.year || '2026',
      visibility: 'public'
    };

    // Enviar obra para o ORCID
    const response = await fetch(`${ORCID_API_URL}/${normalizedOrcid}/work`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ORCID_ACCESS_TOKEN}`
      },
      body: JSON.stringify(defaultWorkData)
    });

    if (!response.ok) {
      throw new Error(`Erro ao vincular obra: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Obra vinculada ao ORCID com sucesso!');
    console.log(`- ORCID: ${orcid}`);
    console.log(`- DOI: ${doi}`);
    console.log(`- Put Code: ${data['put-code']}`);
    
    return {
      success: true,
      orcid: orcid,
      doi: doi,
      putCode: data['put-code']
    };
  } catch (error) {
    console.error('❌ Erro ao vincular obra:', error.message);
    return {
      success: false,
      orcid: orcid,
      doi: doi,
      error: error.message
    };
  }
}

/**
 * Função para atualizar o perfil do ORCID
 * @param {string} orcid - ORCID do autor
 * @param {Object} profileData - Dados do perfil (bio, nome, etc.)
 * @returns {Promise<Object>} - Resultado da operação
 */
async function updateORCIDProfile(orcid, profileData = {}) {
  try {
    // Obter token de acesso
    if (!ORCID_ACCESS_TOKEN) {
      await getAccessToken();
    }

    const normalizedOrcid = orcid.replace(/-/g, '').toLowerCase();
    
    // Dados padrão do perfil
    const defaultProfileData = {
      person: {
        name: {
          'given-names': profileData.givenNames || 'Nuno Filipe Fernandes Vieira Cabral',
          'family-name': profileData.familyName || 'e Araújo'
        },
        biography: profileData.bio || 'Pesquisador em Património Cultural Imaterial e Preservação Digital. Coordenador do projeto Atlas Vivo MILK.',
        'external-identifiers': {
          'external-identifier': profileData.externalIds || []
        }
      }
    };

    // Atualizar perfil
    const response = await fetch(`${ORCID_API_URL}/${normalizedOrcid}/person`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ORCID_ACCESS_TOKEN}`
      },
      body: JSON.stringify(defaultProfileData)
    });

    if (!response.ok) {
      throw new Error(`Erro ao atualizar perfil: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Perfil ORCID atualizado com sucesso!');
    console.log(`- ORCID: ${orcid}`);
    
    return {
      success: true,
      orcid: orcid,
      data: data
    };
  } catch (error) {
    console.error('❌ Erro ao atualizar perfil:', error.message);
    return {
      success: false,
      orcid: orcid,
      error: error.message
    };
  }
}

/**
 * Função para adicionar afiliação a um ORCID
 * @param {string} orcid - ORCID do autor
 * @param {Object} affiliation - Dados da afiliação (nome, tipo, etc.)
 * @returns {Promise<Object>} - Resultado da operação
 */
async function addAffiliationToORCID(orcid, affiliation) {
  try {
    // Obter token de acesso
    if (!ORCID_ACCESS_TOKEN) {
      await getAccessToken();
    }

    const normalizedOrcid = orcid.replace(/-/g, '').toLowerCase();
    
    // Dados padrão da afiliação
    const defaultAffiliation = {
      affiliation: {
        name: affiliation.name || 'Associação MILK',
        type: affiliation.type || 'organization',
        'department-name': affiliation.department || 'Investigação e Desenvolvimento',
        'role-title': affiliation.role || 'Coordenador de Projeto',
        'start-date': {
          year: affiliation.startYear || '2024',
          month: affiliation.startMonth || '01',
          day: affiliation.startDay || '01'
        },
        'end-date': affiliation.endDate ? {
          year: affiliation.endYear,
          month: affiliation.endMonth,
          day: affiliation.endDay
        } : null,
        'current': affiliation.current !== false
      }
    };

    // Adicionar afiliação
    const response = await fetch(`${ORCID_API_URL}/${normalizedOrcid}/employment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ORCID_ACCESS_TOKEN}`
      },
      body: JSON.stringify(defaultAffiliation)
    });

    if (!response.ok) {
      throw new Error(`Erro ao adicionar afiliação: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Afiliação adicionada ao ORCID com sucesso!');
    console.log(`- ORCID: ${orcid}`);
    console.log(`- Organização: ${affiliation.name}`);
    
    return {
      success: true,
      orcid: orcid,
      affiliation: affiliation,
      putCode: data['put-code']
    };
  } catch (error) {
    console.error('❌ Erro ao adicionar afiliação:', error.message);
    return {
      success: false,
      orcid: orcid,
      affiliation: affiliation,
      error: error.message
    };
  }
}

/**
 * Função para validar todos os ORCIDs em um repositório
 * @param {string} repoPath - Caminho do repositório
 * @returns {Promise<Object>} - Resultado da validação
 */
async function validateRepositoryORCIDs(repoPath) {
  const fs = require('fs');
  const path = require('path');
  
  try {
    const files = fs.readdirSync(repoPath);
    const orcids = new Set();
    const results = [];
    
    // Procurar ORCIDs em arquivos JSON e MD
    for (const file of files) {
      const filePath = path.join(repoPath, file);
      if (fs.statSync(filePath).isFile()) {
        const content = fs.readFileSync(filePath, 'utf8');
        const orcidMatches = content.match(/000[0-9]{3}-000[0-9]{3}-[0-9]{3}[0-9X]/g) || [];
        orcidMatches.forEach(orcid => orcids.add(orcid));
      }
    }
    
    console.log(`🔍 Encontrados ${orcids.size} ORCIDs únicos no repositório:`);
    
    // Validar cada ORCID
    for (const orcid of orcids) {
      const result = await validateORCID(orcid);
      results.push(result);
      if (!result.valid) {
        console.log(`❌ ORCID inválido: ${orcid} - ${result.error}`);
      }
    }
    
    const validCount = results.filter(r => r.valid).length;
    const invalidCount = results.length - validCount;
    
    return {
      total: results.length,
      valid: validCount,
      invalid: invalidCount,
      results: results
    };
  } catch (error) {
    console.error('❌ Erro ao validar ORCIDs do repositório:', error.message);
    return {
      total: 0,
      valid: 0,
      invalid: 0,
      error: error.message
    };
  }
}

// Exportar funções para uso em outros módulos
module.exports = {
  getAccessToken,
  validateORCID,
  getWorksByORCID,
  linkWorkToORCID,
  updateORCIDProfile,
  addAffiliationToORCID,
  validateRepositoryORCIDs,
  ORCID_API_URL,
  ORCID_PUBLIC_API_URL
};

// Executar como script CLI
if (require.main === module) {
  const args = process.argv.slice(2);
  const command = args[0];
  const orcid = args[1];
  const doi = args[2];

  (async () => {
    try {
      switch (command) {
        case '--validate':
          if (!orcid) {
            console.log('❌ Uso: node orcid_api_integration.js --validate <ORCID>');
            process.exit(1);
          }
          const result = await validateORCID(orcid);
          console.log('\n📋 Resultado:', result);
          break;

        case '--works':
          if (!orcid) {
            console.log('❌ Uso: node orcid_api_integration.js --works <ORCID>');
            process.exit(1);
          }
          const works = await getWorksByORCID(orcid);
          console.log('\n📚 Obras:', works);
          break;

        case '--link':
          if (!orcid || !doi) {
            console.log('❌ Uso: node orcid_api_integration.js --link <ORCID> <DOI>');
            process.exit(1);
          }
          const linkResult = await linkWorkToORCID(orcid, doi);
          console.log('\n🔗 Resultado:', linkResult);
          break;

        case '--update-profile':
          if (!orcid) {
            console.log('❌ Uso: node orcid_api_integration.js --update-profile <ORCID>');
            process.exit(1);
          }
          const profileResult = await updateORCIDProfile(orcid);
          console.log('\n👤 Resultado:', profileResult);
          break;

        case '--add-affiliation':
          if (!orcid) {
            console.log('❌ Uso: node orcid_api_integration.js --add-affiliation <ORCID>');
            process.exit(1);
          }
          const affiliationResult = await addAffiliationToORCID(orcid, {
            name: 'Associação MILK',
            type: 'organization',
            role: 'Coordenador de Projeto'
          });
          console.log('\n🏢 Resultado:', affiliationResult);
          break;

        case '--validate-repo':
          const repoPath = args[1];
          if (!repoPath) {
            console.log('❌ Uso: node orcid_api_integration.js --validate-repo <caminho_repositório>');
            process.exit(1);
          }
          const repoResult = await validateRepositoryORCIDs(repoPath);
          console.log('\n📊 Resultado:', repoResult);
          break;

        default:
          console.log('📖 Uso:');
          console.log('  node orcid_api_integration.js --validate <ORCID>          # Validar ORCID');
          console.log('  node orcid_api_integration.js --works <ORCID>            # Listar obras');
          console.log('  node orcid_api_integration.js --link <ORCID> <DOI>       # Vincular obra');
          console.log('  node orcid_api_integration.js --update-profile <ORCID>  # Atualizar perfil');
          console.log('  node orcid_api_integration.js --add-affiliation <ORCID> # Adicionar afiliação');
          console.log('  node orcid_api_integration.js --validate-repo <path>    # Validar ORCIDs em repositório');
          console.log('\n🔧 Variáveis de ambiente:');
          console.log('  ORCID_CLIENT_ID=seu_client_id');
          console.log('  ORCID_CLIENT_SECRET=seu_client_secret');
          console.log('  ORCID_REDIRECT_URI=seu_redirect_uri');
      }
    } catch (error) {
      console.error('❌ Erro:', error.message);
    }
  })();
}
