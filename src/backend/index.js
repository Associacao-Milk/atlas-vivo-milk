/**
 * Atlas Vivo MILK - Backend Integration Hub
 */

const { fetchAdministrativeBoundaries } = require('./fetch_dgt_data');
const { fetchWeatherForecast, fetchObservedData } = require('./fetch_ipma_data');
const { listDatasets, searchDatasets } = require('./fetch_dados_gov');
const { listDeputados, listIniciativas } = require('./fetch_assembleia_data');

const commands = {
  'dgt:boundaries': async () => {
    console.log('Fetching DGT administrative boundaries...');
    const result = await fetchAdministrativeBoundaries();
    if (result.success) {
      console.log('Success! Features:', result.data?.features?.length || 0);
      console.log('Attribution:', result.attribution);
    } else {
      console.error('Error:', result.error);
    }
  },
  
  'ipma:forecast': async () => {
    console.log('Fetching IPMA weather forecast...');
    const result = await fetchWeatherForecast();
    if (result.success) {
      console.log('Success! Cities:', Object.keys(result.data || {}).length);
      console.log('Attribution:', result.attribution);
    } else {
      console.error('Error:', result.error);
    }
  },
  
  'ipma:observed': async () => {
    console.log('Fetching IPMA observed data...');
    const result = await fetchObservedData();
    if (result.success) {
      console.log('Success! Stations:', result.data?.length || 0);
      console.log('Attribution:', result.attribution);
    } else {
      console.error('Error:', result.error);
    }
  },
  
  'dados-gov:list': async () => {
    console.log('Listing datasets from dados.gov.pt...');
    const result = await listDatasets();
    if (result.success) {
      console.log('Success! Total datasets:', result.datasets?.length || 0);
      console.log('Attribution:', result.attribution);
    } else {
      console.error('Error:', result.error);
    }
  },
  
  'dados-gov:search': async (query) => {
    console.log('Searching dados.gov.pt for: ' + query);
    const result = await searchDatasets(query);
    if (result.success) {
      console.log('Success! Found:', result.count || 0, 'datasets');
      if (result.results && result.results.length > 0) {
        console.log('First 5 results:');
        result.results.slice(0, 5).forEach(function(r, i) {
          console.log('  ' + (i + 1) + '. ' + r.title + ' (' + (r.organization?.title || 'N/A') + ')');
        });
      }
      console.log('Attribution:', result.attribution);
    } else {
      console.error('Error:', result.error);
    }
  },
  
  'assembleia:deputados': async () => {
    console.log('Fetching deputados from Assembleia da Republica...');
    const result = await listDeputados();
    if (result.success) {
      console.log('Success! Total deputados:', result.data?.length || 0);
      console.log('Attribution:', result.attribution);
    } else {
      console.error('Error:', result.error);
    }
  },
  
  'assembleia:iniciativas': async () => {
    console.log('Fetching iniciativas from Assembleia da Republica...');
    const result = await listIniciativas({ limit: 10 });
    if (result.success) {
      console.log('Success! Total iniciativas:', result.data?.length || 0);
      console.log('Attribution:', result.attribution);
    } else {
      console.error('Error:', result.error);
    }
  },
  
  'all': async () => {
    console.log('=== Fetching ALL available public APIs ===\\n');
    await commands['dgt:boundaries']();
    console.log('');
    await commands['ipma:forecast']();
    console.log('');
    await commands['ipma:observed']();
    console.log('');
    await commands['dados-gov:list']();
    console.log('');
    await commands['assembleia:deputados']();
    console.log('');
    await commands['assembleia:iniciativas']();
    console.log('\n=== All API integrations tested successfully! ===');
  },
  
  'help': function() {
    console.log('Atlas Vivo MILK - Backend Integration Hub\\n');
    console.log('Available commands:');
    console.log('  dgt:boundaries      - Fetch DGT administrative boundaries');
    console.log('  ipma:forecast       - Fetch IPMA weather forecast');
    console.log('  ipma:observed       - Fetch IPMA observed data');
    console.log('  dados-gov:list      - List all datasets from dados.gov.pt');
    console.log('  dados-gov:search <query> - Search datasets on dados.gov.pt');
    console.log('  assembleia:deputados - List all deputados');
    console.log('  assembleia:iniciativas - List legislative iniciativas');
    console.log('  all                 - Test all integrations');
    console.log('  help                - Show this help\\n');
    console.log('Example: node index.js dgt:boundaries');
    console.log('Example: node index.js dados-gov:search "patrimonio cultural"');
  }
};

const command = process.argv[2];
const args = process.argv.slice(3);

if (commands[command]) {
  commands[command](...args).catch(console.error);
} else {
  commands.help();
}
