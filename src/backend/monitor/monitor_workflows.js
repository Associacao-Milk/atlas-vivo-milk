/**
 * Atlas Vivo MILK - Monitor de Workflows
 * 
 * @description: Script para monitorar o status dos workflows em todos os repositórios.
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
 *   node monitor_workflows.js
 */

const fetch = require('node-fetch');
const dotenv = require('dotenv');

// Carregar variáveis de ambiente
dotenv.config();

// Configuração
const GITHUB_API_URL = 'https://api.github.com';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const REPOSITORIES = [
  'milkivc/atlas-datasets',
  'milkivc/atlas-docs',
  'milkivc/atlas-vivo-milk'
];

// Workflows a monitorar
const WORKFLOWS = [
  'validate-orcid.yml',
  'sync-zenodo.yml',
  'sync-codeberg.yml'
];

/**
 * Função para obter headers do GitHub
 */
function getGitHubHeaders() {
  return {
    'Authorization': `token ${GITHUB_TOKEN}`,
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'Atlas Vivo MILK Monitor'
  };
}

/**
 * Função para obter o status dos workflows de um repositório
 * @param {string} repo - Nome do repositório (ex: milkivc/atlas-datasets)
 * @returns {Promise<Array>} - Lista de workflows com status
 */
async function getWorkflowRuns(repo) {
  try {
    const response = await fetch(
      `${GITHUB_API_URL}/repos/${repo}/actions/runs?per_page=10`,
      { headers: getGitHubHeaders() }
    );
    
    if (!response.ok) {
      throw new Error(`Erro ao obter workflows: ${response.status} - ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.workflow_runs || [];
  } catch (error) {
    console.error(`❌ Erro ao obter workflows de ${repo}:`, error.message);
    return [];
  }
}

/**
 * Função para obter o nome do workflow a partir do ID
 * @param {string} repo - Nome do repositório
 * @param {number} workflowId - ID do workflow
 * @returns {Promise<string>} - Nome do workflow
 */
async function getWorkflowName(repo, workflowId) {
  try {
    const response = await fetch(
      `${GITHUB_API_URL}/repos/${repo}/actions/workflows/${workflowId}`,
      { headers: getGitHubHeaders() }
    );
    
    if (!response.ok) {
      return `Workflow #${workflowId}`;
    }
    
    const data = await response.json();
    return data.name || `Workflow #${workflowId}`;
  } catch (error) {
    return `Workflow #${workflowId}`;
  }
}

/**
 * Função para monitorar todos os workflows
 */
async function monitorAllWorkflows() {
  console.log('🔍 Monitorando workflows do Atlas Vivo MILK...\n');
  
  for (const repo of REPOSITORIES) {
    console.log(`📦 Repositório: ${repo}`);
    console.log('─'.repeat(50));
    
    const workflowRuns = await getWorkflowRuns(repo);
    
    if (workflowRuns.length === 0) {
      console.log('  ⚠️ Nenhum workflow encontrado (verifique o token)');
      continue;
    }
    
    // Filtrar workflows recentes (últimas 24h)
    const recentRuns = workflowRuns.filter(run => {
      const runDate = new Date(run.created_at);
      const now = new Date();
      const hoursDiff = (now - runDate) / (1000 * 60 * 60);
      return hoursDiff <= 24;
    });
    
    if (recentRuns.length === 0) {
      console.log('  ℹ️ Nenhum workflow executado nas últimas 24h');
      continue;
    }
    
    // Ordenar por data (mais recente primeiro)
    recentRuns.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    for (const run of recentRuns) {
      const workflowName = await getWorkflowName(repo, run.workflow_id);
      const status = run.status;
      const conclusion = run.conclusion;
      const createdAt = new Date(run.created_at).toLocaleString('pt-PT');
      const duration = run.run_duration_ms ? `${(run.run_duration_ms / 1000).toFixed(1)}s` : 'N/A';
      
      // Definir emoji com base no status
      let emoji;
      switch (conclusion) {
        case 'success':
          emoji = '✅';
          break;
        case 'failure':
          emoji = '❌';
          break;
        case 'cancelled':
          emoji = '⚠️';
          break;
        default:
          emoji = status === 'completed' ? '✅' : '⏳';
      }
      
      console.log(`  ${emoji} ${workflowName}`);
      console.log(`     Status: ${status} | Conclusão: ${conclusion || 'N/A'}`);
      console.log(`     Iniciado: ${createdAt} | Duração: ${duration}`);
      console.log(`     URL: https://github.com/${repo}/actions/runs/${run.id}`);
      console.log('');
    }
    
    console.log('');
  }
}

/**
 * Função para verificar se um workflow específico está funcionando
 * @param {string} repo - Nome do repositório
 * @param {string} workflowName - Nome do workflow
 * @returns {Promise<Object>} - Status do workflow
 */
async function checkWorkflowStatus(repo, workflowName) {
  try {
    // Obter todos os workflows do repositório
    const response = await fetch(
      `${GITHUB_API_URL}/repos/${repo}/actions/workflows`,
      { headers: getGitHubHeaders() }
    );
    
    if (!response.ok) {
      throw new Error(`Erro ao obter workflows: ${response.status}`);
    }
    
    const workflows = await response.json();
    const workflow = workflows.workflows.find(w => w.name === workflowName);
    
    if (!workflow) {
      return { exists: false, error: `Workflow ${workflowName} não encontrado` };
    }
    
    // Obter as últimas execuções
    const runsResponse = await fetch(
      `${GITHUB_API_URL}/repos/${repo}/actions/workflows/${workflow.id}/runs?per_page=5`,
      { headers: getGitHubHeaders() }
    );
    
    const runs = await runsResponse.json();
    const lastRun = runs.workflow_runs[0];
    
    if (!lastRun) {
      return { exists: true, status: 'never_run' };
    }
    
    return {
      exists: true,
      status: lastRun.status,
      conclusion: lastRun.conclusion,
      created_at: lastRun.created_at,
      html_url: lastRun.html_url
    };
  } catch (error) {
    return { exists: false, error: error.message };
  }
}

/**
 * Função para verificar todos os workflows críticos
 */
async function checkCriticalWorkflows() {
  console.log('🔍 Verificando status dos workflows críticos...\n');
  
  const results = {};
  
  for (const repo of REPOSITORIES) {
    results[repo] = {};
    
    for (const workflow of WORKFLOWS) {
      const workflowName = workflow.replace('.yml', '');
      const status = await checkWorkflowStatus(repo, workflowName);
      results[repo][workflow] = status;
      
      // Exibir status
      const emoji = status.conclusion === 'success' ? '✅' : 
                    status.conclusion === 'failure' ? '❌' : 
                    status.status === 'never_run' ? '⚠️' : '⏳';
      
      console.log(`${emoji} ${repo}/${workflow}: ${status.conclusion || status.status || 'N/A'}`);
    }
    
    console.log('');
  }
  
  return results;
}

// Exportar funções para uso em outros módulos
module.exports = {
  getWorkflowRuns,
  getWorkflowName,
  monitorAllWorkflows,
  checkWorkflowStatus,
  checkCriticalWorkflows,
  REPOSITORIES,
  WORKFLOWS
};

// Executar como script CLI
if (require.main === module) {
  const args = process.argv.slice(2);
  const command = args[0];
  
  (async () => {
    try {
      if (command === '--check-critical') {
        await checkCriticalWorkflows();
      } else if (command === '--monitor-all') {
        await monitorAllWorkflows();
      } else {
        console.log('📖 Uso:');
        console.log('  node monitor_workflows.js --check-critical  # Verificar workflows críticos');
        console.log('  node monitor_workflows.js --monitor-all    # Monitorar todos os workflows');
        console.log('\n🔧 Variáveis de ambiente:');
        console.log('  GITHUB_TOKEN=seu_github_token');
      }
    } catch (error) {
      console.error('❌ Erro:', error.message);
    }
  })();
}
