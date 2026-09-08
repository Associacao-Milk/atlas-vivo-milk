/**
 * Atlas Vivo MILK - dados.gov.pt API Integration
 * Immediate access (API key optional)
 */

const axios = require('axios');

const DADOS_GOV_API = 'https://api.dados.gov.pt/api/3/action';

async function listDatasets() {
  try {
    const response = await axios.get(`${DADOS_GOV_API}/package_list`);
    return {
      success: true,
      datasets: response.data.result,
      source: 'dados.gov.pt',
      attribution: 'Fonte: dados.gov.pt - Portal de Dados Abertos de Portugal'
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function searchDatasets(query) {
  try {
    const response = await axios.get(`${DADOS_GOV_API}/package_search?q=${query}`);
    return {
      success: true,
      results: response.data.result.results,
      count: response.data.result.count,
      source: 'dados.gov.pt',
      attribution: 'Fonte: dados.gov.pt'
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

module.exports = { listDatasets, searchDatasets, DADOS_GOV_API };
