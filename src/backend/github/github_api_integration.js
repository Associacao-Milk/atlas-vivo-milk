/**
 * Atlas Vivo MILK - Integração com GitHub API
 * 
 * @description: Script para sincronizar repositórios com o Codeberg e gerenciar workflows.
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
 *   node github_api_integration.js --sync-to-codeberg milkivc/atlas-datasets
 */

const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// Carregar variáveis de ambiente
dotenv.config();

// Configuração das APIs
const GITHUB_API_URL = 'https://api.github.com';
const CODEBERG_API_URL = 'https://codeberg.org/api/v1';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const CODEBERG_TOKEN = process.env.CODEBERG_TOKEN;
const CODEBERG_USER = process.env.CODEBERG_USER || 'milkivc';

// Verificar se os tokens estão configurados
if (!GITHUB_TOKEN) {
  console.warn('⚠️ Aviso: GITHUB_TOKEN não está configurado. Use variáveis de ambiente.');
}
if (!CODEBERG_TOKEN) {
  console.warn('⚠️ Aviso: CODEBERG_TOKEN não está configurado. Use variáveis de ambiente.');
}

/**
 * Função para obter headers do GitHub
 */
function getGitHubHeaders() {
  return {
    'Authorization': `token ${GITHUB_TOKEN}`,
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'Atlas Vivo MILK'
  };
}

/**
 * Função para obter headers do Codeberg
 */
function getCodebergHeaders() {
  return {
    'Authorization': `token ${CODEBERG_TOKEN}`,
    'Accept': 'application/json'
  };
}

/**
 * Função para listar repositórios do GitHub
 * @returns {Promise<Array>} - Lista de repositórios
 */
async function listGitHubRepos() {
  try {
    const response = await fetch(`${GITHUB_API_URL}/user/repos`, {
      headers: getGitHubHeaders()
    });

    if (!response.ok) {
      throw new Error(`Erro ao listar repositórios do GitHub: ${response.status} - ${response.statusText}`);
    }

    const repos = await response.json();
    console.log(`✅ ${repos.length} repositórios encontrados no GitHub:`);
    repos.forEach(repo => {
      console.log(`- ${repo.full_name} (${repo.private ? 'Privado' : 'Público'})`);
    });
    return repos;
  } catch (error) {
    console.error('❌ Erro ao listar repositórios do GitHub:', error.message);
    return [];
  }
}

/**
 * Função para listar repositórios do Codeberg
 * @returns {Promise<Array>} - Lista de repositórios
 */
async function listCodebergRepos() {
  try {
    const response = await fetch(`${CODEBERG_API_URL}/user/repos`, {
      headers: getCodebergHeaders()
    });

    if (!response.ok) {
      throw new Error(`Erro ao listar repositórios do Codeberg: ${response.status} - ${response.statusText}`);
    }

    const repos = await response.json();
    console.log(`✅ ${repos.length} repositórios encontrados no Codeberg:`);
    repos.forEach(repo => {
      console.log(`- ${repo.full_name} (${repo.private ? 'Privado' : 'Público'})`);
    });
    return repos;
  } catch (error) {
    console.error('❌ Erro ao listar repositórios do Codeberg:', error.message);
    return [];
  }
}

/**
 * Função para criar um repositório no Codeberg
 * @param {string} name - Nome do repositório
 * @param {Object} options - Opções do repositório
 * @returns {Promise<Object>} - Objeto com os dados do repositório criado
 */
async function createCodebergRepo(name, options = {}) {
  try {
    const defaultOptions = {
      description: options.description || 'Repositório do Atlas Vivo MILK',
      private: options.private || false,
      mirror: options.mirror || false,
      has_issues: options.hasIssues || true,
      has_wiki: options.hasWiki || true,
      has_downloads: options.hasDownloads || true
    };

    const response = await fetch(`${CODEBERG_API_URL}/user/repos`, {
      method: 'POST',
      headers: getCodebergHeaders(),
      body: JSON.stringify({
        name: name,
        ...defaultOptions
      })
    });

    if (!response.ok) {
      throw new Error(`Erro ao criar repositório no Codeberg: ${response.status} - ${response.statusText}`);
    }

    const repo = await response.json();
    console.log('✅ Repositório criado no Codeberg com sucesso!');
    console.log(`- Nome: ${repo.full_name}`);
    console.log(`- URL: ${repo.html_url}`);
    console.log(`- Clone URL: ${repo.clone_url}`);
    return repo;
  } catch (error) {
    console.error('❌ Erro ao criar repositório no Codeberg:', error.message);
    return null;
  }
}

/**
 * Função para sincronizar um repositório do GitHub para o Codeberg
 * @param {string} githubRepo - Nome do repositório no GitHub (ex: milkivc/atlas-datasets)
 * @param {Object} options - Opções de sincronização
 * @returns {Promise<Object>} - Resultado da sincronização
 */
async function syncRepoToCodeberg(githubRepo, options = {}) {
  try {
    // 1. Obter informações do repositório do GitHub
    const [owner, name] = githubRepo.split('/');
    const githubResponse = await fetch(`${GITHUB_API_URL}/repos/${githubRepo}`, {
      headers: getGitHubHeaders()
    });

    if (!githubResponse.ok) {
      throw new Error(`Repositório do GitHub não encontrado: ${githubRepo}`);
    }

    const githubRepoData = await githubResponse.json();
    console.log(`🔍 Sincronizando repositório: ${githubRepo}`);
    console.log(`- Descrição: ${githubRepoData.description}`);
    console.log(`- Estrelas: ${githubRepoData.stargazers_count}`);
    console.log(`- Forks: ${githubRepoData.forks_count}`);

    // 2. Criar repositório no Codeberg (se não existir)
    let codebergRepo = null;
    const codebergRepos = await listCodebergRepos();
    const existingRepo = codebergRepos.find(repo => repo.name === name);

    if (existingRepo) {
      codebergRepo = existingRepo;
      console.log(`✅ Repositório já existe no Codeberg: ${existingRepo.full_name}`);
    } else {
      codebergRepo = await createCodebergRepo(name, {
        description: githubRepoData.description || `Mirror de ${githubRepo}`,
        private: githubRepoData.private || false
      });
    }

    // 3. Adicionar remote do Codeberg ao repositório local
    const codebergRepoUrl = codebergRepo.clone_url;
    console.log(`🔗 URL do Codeberg: ${codebergRepoUrl}`);

    // 4. Clonar repositório do GitHub, adicionar remote do Codeberg e fazer push
    const tempDir = `/tmp/${name}_sync`;
    
    // Comandos para executar no terminal (simulação)
    const commands = [
      `mkdir -p ${tempDir}`,
      `cd ${tempDir}`,
      `git clone --mirror https://github.com/${githubRepo}.git`,
      `cd ${name}.git`,
      `git remote add codeberg ${codebergRepoUrl}`,
      `git push --mirror codeberg`
    ];

    console.log('\n📝 Comandos para sincronizar (execute localmente):');
    commands.forEach(cmd => console.log(`  ${cmd}`));

    return {
      success: true,
      githubRepo: githubRepo,
      codebergRepo: codebergRepo.full_name,
      codebergUrl: codebergRepo.html_url,
      commands: commands
    };
  } catch (error) {
    console.error('❌ Erro ao sincronizar repositório:', error.message);
    return {
      success: false,
      githubRepo: githubRepo,
      error: error.message
    };
  }
}

/**
 * Função para sincronizar todos os repositórios do GitHub para o Codeberg
 * @param {Array} repos - Lista de repositórios a sincronizar
 * @returns {Promise<Array>} - Lista de resultados
 */
async function syncAllReposToCodeberg(repos) {
  const results = [];
  
  for (const repo of repos) {
    const result = await syncRepoToCodeberg(repo);
    results.push(result);
    console.log('---');
  }
  
  return results;
}

/**
 * Função para criar um workflow de CI/CD no GitHub
 * @param {string} repo - Nome do repositório (ex: milkivc/atlas-datasets)
 * @param {string} workflowName - Nome do workflow
 * @param {string} workflowContent - Conteúdo do workflow (YAML)
 * @returns {Promise<Object>} - Resultado da criação
 */
async function createGitHubWorkflow(repo, workflowName, workflowContent) {
  try {
    const [owner, name] = repo.split('/');
    const workflowPath = `.github/workflows/${workflowName}`;
    
    // Criar ou atualizar workflow
    const response = await fetch(`${GITHUB_API_URL}/repos/${repo}/contents/${workflowPath}`, {
      method: 'PUT',
      headers: getGitHubHeaders(),
      body: JSON.stringify({
        message: `feat: adicionar workflow ${workflowName}`,
        content: Buffer.from(workflowContent).toString('base64')
      })
    });

    if (!response.ok) {
      throw new Error(`Erro ao criar workflow: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Workflow criado com sucesso!');
    console.log(`- Repositório: ${repo}`);
    console.log(`- Workflow: ${workflowName}`);
    console.log(`- URL: ${data.content.html_url}`);
    
    return {
      success: true,
      repo: repo,
      workflow: workflowName,
      url: data.content.html_url
    };
  } catch (error) {
    console.error('❌ Erro ao criar workflow:', error.message);
    return {
      success: false,
      repo: repo,
      workflow: workflowName,
      error: error.message
    };
  }
}

/**
 * Função para criar workflow de validação de ORCID
 * @param {string} repo - Nome do repositório
 * @returns {Promise<Object>} - Resultado da criação
 */
async function createORCIDValidationWorkflow(repo) {
  const workflowContent = `name: Validate ORCIDs

on:
  push:
    paths:
      - '**.json'
      - '**.md'
  pull_request:
    paths:
      - '**.json'
      - '**.md'

jobs:
  validate-orcids:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm install node-fetch dotenv

      - name: Validate ORCIDs
        run: |
          node -e "
            const fs = require('fs');
            const path = require('path');
            
            // Função para validar ORCID
            function validateORCID(orcid) {
              const normalized = orcid.replace(/-/g, '').toLowerCase();
              if (!/^[0-9]{16}$/.test(normalized)) {
                console.error('❌ ORCID inválido:', orcid);
                return false;
              }
              console.log('✅ ORCID válido:', orcid);
              return true;
            }
            
            // Procurar ORCIDs em arquivos
            const files = fs.readdirSync('.');
            let allValid = true;
            
            files.forEach(file => {
              const filePath = path.join('.', file);
              if (fs.statSync(filePath).isFile()) {
                const content = fs.readFileSync(filePath, 'utf8');
                const orcidMatches = content.match(/000[0-9]{3}-000[0-9]{3}-[0-9]{3}[0-9X]/g) || [];
                orcidMatches.forEach(orcid => {
                  if (!validateORCID(orcid)) {
                    allValid = false;
                  }
                });
              }
            });
            
            if (!allValid) {
              process.exit(1);
            }
          "

      - name: Check for placeholder ORCIDs
        run: |
          if grep -r "0000-0000-0000-0000" .; then
            echo "❌ ORCID placeholder encontrado!"
            exit 1
          else
            echo "✅ Nenhum ORCID placeholder encontrado"
          fi
`;

  return createGitHubWorkflow(repo, 'validate-orcid.yml', workflowContent);
}

/**
 * Função para criar workflow de sincronização com Zenodo
 * @param {string} repo - Nome do repositório
 * @returns {Promise<Object>} - Resultado da criação
 */
async function createZenodoSyncWorkflow(repo) {
  const workflowContent = `name: Sync with Zenodo

on:
  push:
    tags:
      - 'v*'

jobs:
  sync-zenodo:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm install node-fetch dotenv

      - name: Deposit to Zenodo
        env:
          ZENODO_TOKEN: ">${{ secrets.ZENODO_TOKEN }}"
        run: |
          node -e "
            const { depositRepository } = require('./src/backend/zenodo/zenodo_api_integration.js');
            const path = require('path');
            
            const repoPath = path.resolve('.');
            const result = await depositRepository(repoPath);
            
            if (result.success) {
              console.log('✅ Depósito no Zenodo concluído!');
              console.log('DOI:', result.doi);
              console.log('URL:', result.url);
              
              // Atualizar metadata.json com DOI
              const metadataPath = path.join(repoPath, 'metadata.json');
              const metadata = require(metadataPath);
              metadata.doi = result.doi;
              fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
              
              // Fazer commit com DOI
              const execSync = require('child_process').execSync;
              execSync('git config --global user.name \"github-actions\"');
              execSync('git config --global user.email \"actions@github.com\"');
              execSync('git add metadata.json');
              execSync('git commit -m \"feat: adicionar DOI do Zenodo [${{ github.sha }}]\"');
              execSync('git push');
            } else {
              console.error('❌ Falha no depósito:', result.error);
              process.exit(1);
            }
          "
`;

  return createGitHubWorkflow(repo, 'sync-zenodo.yml', workflowContent);
}

/**
 * Função para criar workflow de sincronização com Codeberg
 * @param {string} repo - Nome do repositório
 * @returns {Promise<Object>} - Resultado da criação
 */
async function createCodebergSyncWorkflow(repo) {
  const workflowContent = `name: Sync with Codeberg

on:
  push:
    branches:
      - master
      - main

jobs:
  sync-codeberg:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Sync to Codeberg
        env:
          CODEBERG_TOKEN: ">${{ secrets.CODEBERG_TOKEN }}"
          CODEBERG_USER: ">${{ secrets.CODEBERG_USER }}"
          CODEBERG_REPO: ">${{ secrets.CODEBERG_REPO }}"
        run: |
          # Configurar remote do Codeberg
          git remote add codeberg https://${{ secrets.CODEBERG_USER }}:${{ secrets.CODEBERG_TOKEN }}@codeberg.org/${{ secrets.CODEBERG_USER }}/${{ secrets.CODEBERG_REPO }}.git
          
          # Fazer push para o Codeberg
          git push --mirror codeberg
          
          echo "✅ Sincronização com Codeberg concluída!"
`;

  return createGitHubWorkflow(repo, 'sync-codeberg.yml', workflowContent);
}

/**
 * Função para criar todos os workflows em um repositório
 * @param {string} repo - Nome do repositório
 * @returns {Promise<Array>} - Lista de resultados
 */
async function createAllWorkflows(repo) {
  const results = [];
  
  console.log(`🚀 Criando workflows para ${repo}...`);
  
  // Workflow de validação de ORCID
  const orcidWorkflow = await createORCIDValidationWorkflow(repo);
  results.push(orcidWorkflow);
  
  // Workflow de sincronização com Zenodo
  const zenodoWorkflow = await createZenodoSyncWorkflow(repo);
  results.push(zenodoWorkflow);
  
  // Workflow de sincronização com Codeberg
  const codebergWorkflow = await createCodebergSyncWorkflow(repo);
  results.push(codebergWorkflow);
  
  return results;
}

// Exportar funções para uso em outros módulos
module.exports = {
  listGitHubRepos,
  listCodebergRepos,
  createCodebergRepo,
  syncRepoToCodeberg,
  syncAllReposToCodeberg,
  createGitHubWorkflow,
  createORCIDValidationWorkflow,
  createZenodoSyncWorkflow,
  createCodebergSyncWorkflow,
  createAllWorkflows,
  getGitHubHeaders,
  getCodebergHeaders,
  GITHUB_API_URL,
  CODEBERG_API_URL
};

// Executar como script CLI
if (require.main === module) {
  const args = process.argv.slice(2);
  const command = args[0];
  const repo = args[1];

  (async () => {
    try {
      switch (command) {
        case '--list-github':
          const githubRepos = await listGitHubRepos();
          console.log('\n📊 Repositórios do GitHub:', githubRepos);
          break;

        case '--list-codeberg':
          const codebergRepos = await listCodebergRepos();
          console.log('\n📊 Repositórios do Codeberg:', codebergRepos);
          break;

        case '--sync':
          if (!repo) {
            console.log('❌ Uso: node github_api_integration.js --sync <github_repo>');
            process.exit(1);
          }
          const syncResult = await syncRepoToCodeberg(repo);
          console.log('\n🔄 Resultado:', syncResult);
          break;

        case '--sync-all':
          const allRepos = await listGitHubRepos();
          const reposToSync = allRepos
            .filter(repo => repo.name.startsWith('atlas-'))
            .map(repo => repo.full_name);
          const syncAllResult = await syncAllReposToCodeberg(reposToSync);
          console.log('\n🔄 Resultado da sincronização em massa:', syncAllResult);
          break;

        case '--create-workflows':
          if (!repo) {
            console.log('❌ Uso: node github_api_integration.js --create-workflows <github_repo>');
            process.exit(1);
          }
          const workflowsResult = await createAllWorkflows(repo);
          console.log('\n📝 Workflows criados:', workflowsResult);
          break;

        default:
          console.log('📖 Uso:');
          console.log('  node github_api_integration.js --list-github          # Listar repositórios do GitHub');
          console.log('  node github_api_integration.js --list-codeberg        # Listar repositórios do Codeberg');
          console.log('  node github_api_integration.js --sync <repo>          # Sincronizar repositório para Codeberg');
          console.log('  node github_api_integration.js --sync-all             # Sincronizar todos os repositórios');
          console.log('  node github_api_integration.js --create-workflows <repo> # Criar workflows');
          console.log('\n🔧 Variáveis de ambiente:');
          console.log('  GITHUB_TOKEN=seu_github_token');
          console.log('  CODEBERG_TOKEN=seu_codeberg_token');
          console.log('  CODEBERG_USER=seu_usuario_codeberg');
      }
    } catch (error) {
      console.error('❌ Erro:', error.message);
    }
  })();
}
