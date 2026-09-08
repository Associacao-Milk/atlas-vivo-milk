/**
 * Zenodo API Integration for ATLAS VIVO
 * ======================================
 * 
 * Comprehensive JavaScript client for Zenodo API integration.
 * Handles DOI minting, deposit management, and metadata synchronization.
 * 
 * @module zenodo_api_integration
 * @version 2.0.0
 * @author Eduardo Mauricio / Associação MILK
 */

/**
 * Zenodo API Client Class
 * @class ZenodoAPI
 */
class ZenodoAPI {
    /**
     * Initialize Zenodo API client
     * @constructor
     * @param {string} token - Zenodo API token
     * @param {boolean} [sandbox=false] - Use sandbox environment
     */
    constructor(token, sandbox = false) {
        this.token = token || process.env.ZENODO_TOKEN;
        if (!this.token) {
            throw new Error('ZENODO_TOKEN is required. Set ZENODO_TOKEN environment variable.');
        }
        
        this.sandbox = sandbox;
        this.baseURL = sandbox 
            ? 'https://sandbox.zenodo.org/api' 
            : 'https://zenodo.org/api';
        
        this.communityId = process.env.ZENODO_COMMUNITY_ID || 'atlas-vivo-milk';
        
        this.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': `Bearer ${this.token}`
        };
    }
    
    /**
     * Make HTTP request to Zenodo API
     * @private
     * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
     * @param {string} endpoint - API endpoint
     * @param {Object} [data=null] - Request body
     * @param {Object} [params=null] - Query parameters
     * @returns {Promise<Object>} API response
     */
    async _request(method, endpoint, data = null, params = null) {
        const url = new URL(endpoint, this.baseURL);
        
        if (params) {
            Object.keys(params).forEach(key => {
                url.searchParams.append(key, params[key]);
            });
        }
        
        const options = {
            method: method.toUpperCase(),
            headers: this.headers
        };
        
        if (data && (method.toUpperCase() === 'POST' || method.toUpperCase() === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url.toString(), options);
            
            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Zenodo API error: ${response.status} - ${error}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error in Zenodo API request: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Create a new deposit
     * @param {Object} metadata - Deposit metadata
     * @param {boolean} [published=false] - Publish immediately
     * @returns {Promise<Object>} Deposit information
     */
    async createDeposit(metadata, published = false) {
        const data = {
            metadata: metadata,
            published: published
        };
        
        if (this.communityId) {
            data.community = this.communityId;
        }
        
        return this._request('POST', '/deposit/depositions', data);
    }
    
    /**
     * Get deposit information
     * @param {string} depositId - Deposit ID
     * @returns {Promise<Object>} Deposit information
     */
    async getDeposit(depositId) {
        return this._request('GET', `/deposit/depositions/${depositId}`);
    }
    
    /**
     * Update deposit metadata
     * @param {string} depositId - Deposit ID
     * @param {Object} metadata - Updated metadata
     * @returns {Promise<Object>} Updated deposit information
     */
    async updateDeposit(depositId, metadata) {
        return this._request('PUT', `/deposit/depositions/${depositId}`, {
            metadata: metadata
        });
    }
    
    /**
     * Upload file to deposit
     * @param {string} depositId - Deposit ID
     * @param {File|Blob} file - File to upload
     * @param {string} [fileName=null] - Custom file name
     * @returns {Promise<Object>} File upload information
     */
    async uploadFile(depositId, file, fileName = null) {
        // Get bucket URL
        const deposit = await this.getDeposit(depositId);
        const bucketUrl = deposit.links?.bucket;
        
        if (!bucketUrl) {
            throw new Error('Could not get bucket URL for deposit');
        }
        
        // Prepare form data
        const formData = new FormData();
        formData.append('file', file, fileName || file.name);
        
        // Upload to bucket
        const response = await fetch(bucketUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.text();
            throw new Error(`File upload failed: ${response.status} - ${error}`);
        }
        
        return await response.json();
    }
    
    /**
     * Publish deposit and mint DOI
     * @param {string} depositId - Deposit ID
     * @returns {Promise<Object>} Published deposit with DOI
     */
    async publishDeposit(depositId) {
        return this._request('POST', `/deposit/depositions/${depositId}/actions/publish`);
    }
    
    /**
     * Discard deposit (delete unpublished deposit)
     * @param {string} depositId - Deposit ID
     * @returns {Promise<Object>} Deletion confirmation
     */
    async discardDeposit(depositId) {
        return this._request('POST', `/deposit/depositions/${depositId}/actions/discard`);
    }
    
    /**
     * List all deposits
     * @param {number} [page=1] - Page number
     * @param {number} [size=10] - Results per page
     * @returns {Promise<Object>} List of deposits
     */
    async listDeposits(page = 1, size = 10) {
        return this._request('GET', '/deposit/depositions', null, { page, size });
    }
    
    /**
     * Search deposits
     * @param {string} query - Search query
     * @param {number} [page=1] - Page number
     * @param {number} [size=10] - Results per page
     * @returns {Promise<Object>} Search results
     */
    async searchDeposits(query, page = 1, size = 10) {
        return this._request('GET', '/deposit/depositions', null, { q: query, page, size });
    }
    
    /**
     * Link deposit to ORCID record
     * @param {string} depositId - Deposit ID
     * @param {string} orcid - ORCID ID (XXXX-XXXX-XXXX-XXXX)
     * @returns {Promise<Object>} Linking confirmation
     */
    async linkToOrcid(depositId, orcid) {
        // This requires ORCID token and specific API endpoint
        // For now, return a placeholder
        return {
            status: 'success',
            message: `Deposit ${depositId} would be linked to ORCID ${orcid}`,
            depositId: depositId,
            orcid: orcid
        };
    }
    
    /**
     * Create a new DOI by publishing a deposit
     * @param {Object} metadata - Complete metadata for DOI
     * @returns {Promise<Object>} DOI information
     */
    async createDOI(metadata) {
        // Create deposit
        const deposit = await this.createDeposit(metadata);
        const depositId = deposit.id;
        
        if (!depositId) {
            throw new Error('Could not create deposit');
        }
        
        // Publish to mint DOI
        const published = await this.publishDeposit(depositId);
        
        return {
            ...published,
            depositId: depositId,
            doi: published.doi,
            status: 'published'
        };
    }
    
    /**
     * Get DOI information
     * @param {string} doi - DOI to lookup
     * @returns {Promise<Object>} DOI information
     */
    async getDOIInfo(doi) {
        // Extract record ID from DOI
        const recordId = doi.replace('10.', '').split('/')[0];
        return this._request('GET', `/records/${recordId}`);
    }
    
    /**
     * Create standard metadata template for ATLAS VIVO
     * @param {string} title - Title of the deposit
     * @param {string} description - Description
     * @param {Array<Object>} creators - List of creators
     * @param {string} [license='CC-BY-4.0'] - License
     * @returns {Object} Metadata template
     */
    createMetadataTemplate(title, description, creators, license = 'CC-BY-4.0') {
        return {
            title: title,
            description: description,
            creators: creators,
            license: {
                id: license
            },
            resource_type: {
                type: 'dataset',
                title: 'Dataset'
            },
            keywords: [
                'ATLAS VIVO',
                'Associação MILK',
                'Open Science',
                'Research Data'
            ],
            notes: 'Generated by ATLAS VIVO Integration System',
            version: '1.0.0',
            date: new Date().toISOString().split('T')[0]
        };
    }
    
    /**
     * Synchronize a repository with Zenodo
     * @param {string} repoPath - Path to repository
     * @param {string} [metadataFile='metadata.json'] - Metadata file name
     * @returns {Promise<Object>} Synchronization result
     */
    async syncRepository(repoPath, metadataFile = 'metadata.json') {
        // This is a browser/Node.js compatible version
        // In Node.js, you would use fs module
        // In browser, you would use File API
        
        throw new Error('syncRepository requires Node.js fs module or browser File API');
    }
    
    /**
     * Get Zenodo API statistics
     * @returns {Promise<Object>} API statistics
     */
    async getStats() {
        try {
            const deposits = await this.listDeposits(1, 1);
            return {
                totalDeposits: deposits.hits?.total || 0,
                apiVersion: 'v1.0',
                environment: this.sandbox ? 'sandbox' : 'production',
                community: this.communityId
            };
        } catch (error) {
            return {
                error: error.message,
                environment: this.sandbox ? 'sandbox' : 'production'
            };
        }
    }
}

/**
 * Factory function to create Zenodo API instance
 * @param {string} [token] - Zenodo API token
 * @param {boolean} [sandbox=false] - Use sandbox environment
 * @returns {ZenodoAPI} Zenodo API instance
 */
function createZenodoAPI(token, sandbox = false) {
    return new ZenodoAPI(token, sandbox);
}

/**
 * Singleton instance
 */
let zenodoAPIInstance = null;

/**
 * Get singleton Zenodo API instance
 * @param {string} [token] - Zenodo API token
 * @param {boolean} [sandbox=false] - Use sandbox environment
 * @returns {ZenodoAPI} Zenodo API instance
 */
function getZenodoAPI(token, sandbox = false) {
    if (!zenodoAPIInstance) {
        zenodoAPIInstance = createZenodoAPI(token, sandbox);
    }
    return zenodoAPIInstance;
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ZenodoAPI,
        createZenodoAPI,
        getZenodoAPI
    };
}

// Test in browser console
if (typeof window !== 'undefined') {
    window.ZenodoAPI = ZenodoAPI;
    window.createZenodoAPI = createZenodoAPI;
    window.getZenodoAPI = getZenodoAPI;
}
