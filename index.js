/**
 * ATLAS VIVO - Integration APIs Index
 * ====================================
 * 
 * Main entry point for all integration APIs.
 * 
 * @module index
 * @version 2.0.0
 * @author Eduardo Mauricio / Associação MILK
 */

// Import all API modules
const zenodoAPI = require('./zenodo_api_integration.js');
const orcidAPI = require('./orcid_api_integration.js');
const githubAPI = require('./github_api_integration.js');

/**
 * ATLAS VIVO Integration APIs
 * @namespace ATLASVIVO
 */
const ATLASVIVO = {
    // Zenodo API
    ZenodoAPI: zenodoAPI.ZenodoAPI,
    createZenodoAPI: zenodoAPI.createZenodoAPI,
    getZenodoAPI: zenodoAPI.getZenodoAPI,
    
    // ORCID API
    ORCIDAPI: orcidAPI.ORCIDAPI,
    createORCIDAPI: orcidAPI.createORCIDAPI,
    getORCIDAPI: orcidAPI.getORCIDAPI,
    
    // GitHub API
    GitHubAPI: githubAPI.GitHubAPI,
    CodebergAPI: githubAPI.CodebergAPI,
    createGitHubAPI: githubAPI.createGitHubAPI,
    createCodebergAPI: githubAPI.createCodebergAPI,
    getGitHubAPI: githubAPI.getGitHubAPI,
    getCodebergAPI: githubAPI.getCodebergAPI
};

/**
 * Initialize all APIs with environment variables
 * @returns {Object} All API instances
 */
function initAllAPIs() {
    return {
        zenodo: ATLASVIVO.getZenodoAPI(),
        orcid: ATLASVIVO.getORCIDAPI(),
        github: ATLASVIVO.getGitHubAPI(),
        codeberg: ATLASVIVO.getCodebergAPI()
    };
}

/**
 * Unified Integration API
 * @class UnifiedAPI
 */
class UnifiedAPI {
    /**
     * Initialize unified API
     * @constructor
     * @param {Object} [options] - Configuration options
     */
    constructor(options = {}) {
        this.zenodo = ATLASVIVO.getZenodoAPI(options.zenodoToken, options.sandbox);
        this.orcid = ATLASVIVO.getORCIDAPI({
            clientId: options.orcidClientId,
            clientSecret: options.orcidClientSecret,
            token: options.orcidToken,
            sandbox: options.sandbox
        });
        this.github = ATLASVIVO.getGitHubAPI({ token: options.githubToken });
        this.codeberg = ATLASVIVO.getCodebergAPI({ token: options.codebergToken });
    }
    
    /**
     * Get all API statistics
     * @returns {Promise<Object>} Statistics from all APIs
     */
    async getAllStats() {
        const [zenodoStats, orcidStats, githubStats, codebergStats] = await Promise.all([
            this.zenodo.getStats(),
            this.orcid.getStats(),
            this.github.getStats(),
            this.codeberg.getStats()
        ]);
        
        return {
            zenodo: zenodoStats,
            orcid: orcidStats,
            github: githubStats,
            codeberg: codebergStats,
            timestamp: new Date().toISOString()
        };
    }
    
    /**
     * Create a complete deposit with DOI and link to ORCIDs
     * @param {Object} metadata - Deposit metadata
     * @param {Array<string>} orcids - ORCID IDs to link
     * @returns {Promise<Object>} Complete operation result
     */
    async createDepositAndLink(metadata, orcids = []) {
        // Create deposit and publish to get DOI
        const depositResult = await this.zenodo.createDOI(metadata);
        
        if (!depositResult.doi) {
            throw new Error('Failed to create DOI');
        }
        
        // Create work payload for ORCID
        const workPayload = this.orcid.createWorkPayload(
            metadata.title,
            depositResult.doi,
            `https://doi.org/${depositResult.doi}`,
            'dataset',
            new Date().toISOString().split('T')[0]
        );
        
        // Link to all ORCIDs
        const linkResults = await this.orcid.linkMultipleOrcids(workPayload, orcids);
        
        return {
            deposit: depositResult,
            orcidLinks: linkResults,
            status: 'success',
            timestamp: new Date().toISOString()
        };
    }
    
    /**
     * Synchronize all repositories with metadata
     * @param {Array<string>} repos - Repository names
     * @param {Object} metadata - Metadata to sync
     * @returns {Promise<Object>} Sync results
     */
    async syncAllRepositories(repos, metadata) {
        const results = {};
        
        // Sync with GitHub
        results.github = await this.github.syncRepositories(repos, metadata);
        
        // Sync with Codeberg (if repos exist there)
        try {
            results.codeberg = await this.codeberg.syncRepositories(repos, metadata);
        } catch (error) {
            results.codeberg = { error: error.message };
        }
        
        return results;
    }
}

// Export everything
ATLASVIVO.UnifiedAPI = UnifiedAPI;
ATLASVIVO.initAllAPIs = initAllAPIs;

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ATLASVIVO;
}

// Export for browser
if (typeof window !== 'undefined') {
    window.ATLASVIVO = ATLASVIVO;
}

// Test in Node.js
if (typeof require !== 'undefined' && require.main === module) {
    console.log('ATLAS VIVO Integration APIs');
    console.log('==========================');
    console.log('All APIs loaded successfully!');
    console.log('');
    console.log('Available APIs:');
    console.log('  - ZenodoAPI');
    console.log('  - ORCIDAPI');
    console.log('  - GitHubAPI');
    console.log('  - CodebergAPI');
    console.log('  - UnifiedAPI');
    console.log('');
    console.log('Usage:');
    console.log('  const { getZenodoAPI, getGitHubAPI } = require("atlas-vivo-integration-apis");');
    console.log('  const zenodo = getZenodoAPI(process.env.ZENODO_TOKEN);');
    console.log('  const github = getGitHubAPI(process.env.GITHUB_TOKEN);');
}
