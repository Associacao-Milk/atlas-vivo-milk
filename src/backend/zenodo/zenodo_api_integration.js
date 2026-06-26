/**
 * Atlas Vivo MILK - Integração com Zenodo API
 * 
 * @description: Script para depositar automaticamente dados no Zenodo e obter DOI.
 * @author: Nuno Filipe Fernandes Vieira Cabral e Araújo (ORCID: 0009-0009-1781-4020)
 * @author: Eduardo Maurício Vieira Cabral e Araújo (ORCID: 0009-0007-6892-6570)
 * @license: EUPL-1.2
 * @version: 1.0.0
 * @date: 2026-06-25
 * 
 * @depends: 
 *   - node-fetch (para requisições HTTP)
 *   - dotenv (para variáveis de ambiente)
 *   - fs (para manipulação de arquivos)
 * 
 * @usage: 
 *   node zenodo_api_integration.js --repo atlas-datasets --file metadata.json
 */

const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// Carregar variáveis de ambiente (ZENODO_TOKEN)
dotenv.config();

// Configuração do Zenodo API
const ZENODO_API_URL = 'https://zenodo.org/api';
const ZENODO_TOKEN = process.env.ZENODO_TOKEN;

// Verificar se o token está configurado
if (!ZENODO_TOKEN) {
  console.warn('⚠️ Aviso: ZENODO_TOKEN não está configurado. Use variáveis de ambiente.');
}

// Metadados padrão para todos os depósitos
const DEFAULT_METADATA = {
  upload_type: 'dataset',
  title: 'Atlas Vivo MILK - Dados de Património Cultural Imaterial',
  description: 'Conjunto de dados geospaciais e culturais do Atlas Vivo MILK, incluindo rituais, lendas e património imaterial português.',
  creators: [
    {
      name: 'Nuno Filipe Fernandes Vieira Cabral e Araújo',
      orcid: '0009-0009-1781-4020',
      affiliation: 'Associação MILK / Universidade de Coimbra'
    },
    {
      name: 'Eduardo Maurício Vieira Cabral e Araújo',
      orcid: '0009-0007-6892-6570',
      affiliation: 'Associação MILK / Instituto Politécnico de Leiria'
    }
  ],
  keywords: [
    'Património Cultural Imaterial',
    'Portugal',
    'Geospacial',
    'CIDOC-CRM',
    'XMP',
    'IPTC',
    'Atlas Vivo MILK',
    'PCI',
    'UNESCO'
  ],
  license: 'CC-BY-SA-4.0',
  version: '1.0.0',
  communities: [
    { identifier: 'zenodo' },
    { identifier: 'europeana' },
    { identifier: 'dariah' }
  ],
  related_identifiers: [
    {
      identifier: '10.5281/zenodo.XXXXXXX',
      relation: 'isPartOf',
      scheme: 'doi'
    }
  ],
  dates: [
    {
      date: '2026-06-25',
      type: 'created'
    },
    {
      date: '2026-06-25',
      type: 'published'
    }
  ],
  language: 'pt-PT',
  notes: 'Dados coletados pelo projeto Atlas Vivo MILK (www.atlas-vivo.milk).',
  access_right: 'open',
  access_conditions: 'CC-BY-SA-4.0',
  embargo_date: null,
  embargo_reason: null
};

/**
 * Função para criar um novo depósito no Zenodo
 * @param {Object} metadata - Metadados do depósito
 * @returns {Promise<Object>} - Objeto com o ID do depósito
 */
async function createDeposition(metadata) {
  try {
    const response = await fetch(`${ZENODO_API_URL}/deposit/depositions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ZENODO_TOKEN}`
      },
      body: JSON.stringify(metadata)
    });

    if (!response.ok) {
      throw new Error(`Erro ao criar depósito: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Depósito criado com sucesso!');
    console.log(`🔗 ID do Depósito: ${data.id}`);
    console.log(`🔗 Link: ${data.links.html}`);
    return data;
  } catch (error) {
    console.error('❌ Erro ao criar depósito:', error.message);
    throw error;
  }
}

/**
 * Função para fazer upload de um arquivo para o depósito
 * @param {string} depositionId - ID do depósito
 * @param {string} filePath - Caminho do arquivo local
 * @param {string} fileName - Nome do arquivo no Zenodo
 * @returns {Promise<Object>} - Objeto com o resultado do upload
 */
async function uploadFile(depositionId, filePath, fileName = null) {
  try {
    const fileNameToUse = fileName || path.basename(filePath);
    const fileData = fs.readFileSync(filePath);

    const response = await fetch(`${ZENODO_API_URL}/deposit/depositions/${depositionId}/files/${fileNameToUse}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/octet-stream',
        'Authorization': `Bearer ${ZENODO_TOKEN}`
      },
      body: fileData
    });

    if (!response.ok) {
      throw new Error(`Erro ao fazer upload do arquivo ${fileNameToUse}: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`✅ Arquivo ${fileNameToUse} enviado com sucesso!`);
    return data;
  } catch (error) {
    console.error(`❌ Erro ao enviar arquivo ${filePath}:`, error.message);
    throw error;
  }
}

/**
 * Função para publicar o depósito (obter DOI)
 * @param {string} depositionId - ID do depósito
 * @returns {Promise<Object>} - Objeto com o DOI e metadados
 */
async function publishDeposition(depositionId) {
  try {
    const response = await fetch(`${ZENODO_API_URL}/deposit/depositions/${depositionId}/actions/publish`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ZENODO_TOKEN}`
      }
    });

    if (!response.ok) {
      throw new Error(`Erro ao publicar depósito: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Depósito publicado com sucesso!');
    console.log(`🔗 DOI: ${data.doi}`);
    console.log(`🔗 URL: ${data.links.html}`);
    return data;
  } catch (error) {
    console.error('❌ Erro ao publicar depósito:', error.message);
    throw error;
  }
}

/**
 * Função para atualizar metadados do depósito
 * @param {string} depositionId - ID do depósito
 * @param {Object} metadata - Metadados atualizados
 * @returns {Promise<Object>} - Objeto com os metadados atualizados
 */
async function updateDepositionMetadata(depositionId, metadata) {
  try {
    const response = await fetch(`${ZENODO_API_URL}/deposit/depositions/${depositionId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ZENODO_TOKEN}`
      },
      body: JSON.stringify(metadata)
    });

    if (!response.ok) {
      throw new Error(`Erro ao atualizar metadados: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Metadados atualizados com sucesso!');
    return data;
  } catch (error) {
    console.error('❌ Erro ao atualizar metadados:', error.message);
    throw error;
  }
}

/**
 * Função para listar todos os depósitos
 * @returns {Promise<Array>} - Lista de depósitos
 */
async function listDepositions() {
  try {
    const response = await fetch(`${ZENODO_API_URL}/deposit/depositions`, {
      headers: {
        'Authorization': `Bearer ${ZENODO_TOKEN}`
      }
    });

    if (!response.ok) {
      throw new Error(`Erro ao listar depósitos: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`✅ ${data.length} depósitos encontrados:`);
    data.forEach(dep => {
      console.log(`- ID: ${dep.id}, Título: ${dep.metadata.title}, DOI: ${dep.metadata.doi || 'N/A'}`);
    });
    return data;
  } catch (error) {
    console.error('❌ Erro ao listar depósitos:', error.message);
    throw error;
  }
}

/**
 * Função principal para depositar um repositório completo no Zenodo
 * @param {string} repoPath - Caminho do repositório local
 * @param {Object} customMetadata - Metadados personalizados (opcional)
 */
async function depositRepository(repoPath, customMetadata = {}) {
  try {
    // 1. Ler metadados do repositório (metadata.json)
    const metadataPath = path.join(repoPath, 'metadata.json');
    let repoMetadata = DEFAULT_METADATA;
    
    if (fs.existsSync(metadataPath)) {
      const repoMetadataFile = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
      repoMetadata = {
        ...DEFAULT_METADATA,
        ...repoMetadataFile,
        ...customMetadata
      };
    }

    // 2. Criar depósito no Zenodo
    const deposition = await createDeposition(repoMetadata);
    const depositionId = deposition.id;

    // 3. Fazer upload de todos os arquivos do repositório
    const files = fs.readdirSync(repoPath);
    for (const file of files) {
      const filePath = path.join(repoPath, file);
      if (fs.statSync(filePath).isFile()) {
        await uploadFile(depositionId, filePath, file);
      }
    }

    // 4. Publicar depósito (obter DOI)
    const publishedDeposition = await publishDeposition(depositionId);

    // 5. Retornar resultado
    return {
      success: true,
      depositionId: depositionId,
      doi: publishedDeposition.doi,
      url: publishedDeposition.links.html,
      metadata: repoMetadata
    };
  } catch (error) {
    console.error('❌ Erro ao depositar repositório:', error.message);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Função para depositar um arquivo específico com metadados personalizados
 * @param {string} filePath - Caminho do arquivo
 * @param {Object} metadata - Metadados personalizados
 */
async function depositFile(filePath, metadata) {
  try {
    // 1. Criar depósito
    const deposition = await createDeposition(metadata);
    const depositionId = deposition.id;

    // 2. Fazer upload do arquivo
    await uploadFile(depositionId, filePath);

    // 3. Publicar depósito
    const publishedDeposition = await publishDeposition(depositionId);

    // 4. Retornar resultado
    return {
      success: true,
      depositionId: depositionId,
      doi: publishedDeposition.doi,
      url: publishedDeposition.links.html
    };
  } catch (error) {
    console.error('❌ Erro ao depositar arquivo:', error.message);
    return {
      success: false,
      error: error.message
    };
  }
}

// Exportar funções para uso em outros módulos
module.exports = {
  createDeposition,
  uploadFile,
  publishDeposition,
  updateDepositionMetadata,
  listDepositions,
  depositRepository,
  depositFile,
  DEFAULT_METADATA,
  ZENODO_API_URL
};

// Executar como script CLI
if (require.main === module) {
  const args = process.argv.slice(2);
  const repoPath = args[0];
  const filePath = args[1];

  if (repoPath) {
    console.log(`🚀 Depositando repositório: ${repoPath}`);
    depositRepository(repoPath)
      .then(result => {
        if (result.success) {
          console.log('\n🎉 Depósito concluído com sucesso!');
          console.log(`- DOI: ${result.doi}`);
          console.log(`- URL: ${result.url}`);
        } else {
          console.error('❌ Falha no depósito:', result.error);
        }
      })
      .catch(error => {
        console.error('❌ Erro:', error.message);
      });
  } else if (filePath) {
    console.log(`🚀 Depositando arquivo: ${filePath}`);
    const customMetadata = {
      ...DEFAULT_METADATA,
      title: `Atlas Vivo MILK - ${path.basename(filePath)}`
    };
    depositFile(filePath, customMetadata)
      .then(result => {
        if (result.success) {
          console.log('\n🎉 Depósito concluído com sucesso!');
          console.log(`- DOI: ${result.doi}`);
          console.log(`- URL: ${result.url}`);
        } else {
          console.error('❌ Falha no depósito:', result.error);
        }
      })
      .catch(error => {
        console.error('❌ Erro:', error.message);
      });
  } else {
    console.log('📖 Uso:');
    console.log('  node zenodo_api_integration.js <caminho_repositório>  # Depositar repositório completo');
    console.log('  node zenodo_api_integration.js <caminho_arquivo>      # Depositar arquivo específico');
    console.log('\n🔧 Variáveis de ambiente:');
    console.log('  ZENODO_TOKEN=seu_token_aqui');
  }
}
