/**
 * ORCID API Integration for ATLAS VIVO
 * ======================================
 * 
 * Comprehensive JavaScript client for ORCID API integration.
 * Handles researcher identification, work linking, and profile management.
 * 
 * @module orcid_api_integration
 * @version 2.0.0
 * @author Eduardo Mauricio / Associação MILK
 */

/**
 * ORCID API Client Class
 * @class ORCIDAPI
 */
class ORCIDAPI {
    /**
     * Initialize ORCID API client
     * @constructor
     * @param {Object} options - Configuration options
     * @param {string} options.clientId - ORCID Client ID
     * @param {string} options.clientSecret - ORCID Client Secret
     * @param {string} [options.token] - ORCID Access Token
     * @param {boolean} [options.sandbox=false] - Use sandbox environment
     */
    constructor(options = {}) {
        this.clientId = options.clientId || process.env.ORCID_CLIENT_ID;
        this.clientSecret = options.clientSecret || process.env.ORCID_CLIENT_SECRET;
        this.token = options.token || process.env.ORCID_TOKEN;
        this.sandbox = options.sandbox || false;
        
        if (!this.clientId || !this.clientSecret) {
            throw new Error('ORCID_CLIENT_ID and ORCID_CLIENT_SECRET are required');
        }
        
        this.baseURL = this.sandbox 
            ? 'https://sandbox.orcid.org/v3.0' 
            : 'https://api.orcid.org/v3.0';
        
        this.authURL = this.sandbox 
            ? 'https://sandbox.orcid.org/oauth/token' 
            : 'https://orcid.org/oauth/token';
        
        this.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
        
        // Authenticate if token not provided
        if (!this.token) {
            this._authenticate();
        } else {
            this.headers['Authorization'] = `Bearer ${this.token}`;
        }
    }
    
    /**
     * Authenticate with ORCID using client credentials
     * @private
     */
    async _authenticate() {
        const params = new URLSearchParams();
        params.append('client_id', this.clientId);
        params.append('client_secret', this.clientSecret);
        params.append('grant_type', 'client_credentials');
        params.append('scope', '/read-limited /activities/update /person/update');
        
        try {
            const response = await fetch(this.authURL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: params.toString()
            });
            
            if (!response.ok) {
                const error = await response.text();
                throw new Error(`ORCID authentication failed: ${response.status} - ${error}`);
            }
            
            const result = await response.json();
            this.token = result.access_token;
            this.headers['Authorization'] = `Bearer ${this.token}`;
            
        } catch (error) {
            console.error(`ORCID authentication error: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Make HTTP request to ORCID API
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
                throw new Error(`ORCID API error: ${response.status} - ${error}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error in ORCID API request: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Get researcher information
     * @param {string} orcid - ORCID ID (XXXX-XXXX-XXXX-XXXX)
     * @returns {Promise<Object>} Researcher information
     */
    async getResearcher(orcid) {
        return this._request('GET', `/${orcid}`);
    }
    
    /**
     * Get researcher's works
     * @param {string} orcid - ORCID ID
     * @returns {Promise<Object>} List of works
     */
    async getResearcherWorks(orcid) {
        return this._request('GET', `/${orcid}/works`);
    }
    
    /**
     * Get specific work information
     * @param {string} orcid - ORCID ID
     * @param {string} workId - Work ID
     * @returns {Promise<Object>} Work information
     */
    async getWork(orcid, workId) {
        return this._request('GET', `/${orcid}/works/${workId}`);
    }
    
    /**
     * Add a work to researcher's ORCID record
     * @param {string} orcid - ORCID ID
     * @param {Object} workData - Work data
     * @returns {Promise<Object>} Created work information
     */
    async addWork(orcid, workData) {
        return this._request('POST', `/${orcid}/works`, workData);
    }
    
    /**
     * Update a work in researcher's ORCID record
     * @param {string} orcid - ORCID ID
     * @param {string} workId - Work ID
     * @param {Object} workData - Updated work data
     * @returns {Promise<Object>} Updated work information
     */
    async updateWork(orcid, workId, workData) {
        return this._request('PUT', `/${orcid}/works/${workId}`, workData);
    }
    
    /**
     * Delete a work from researcher's ORCID record
     * @param {string} orcid - ORCID ID
     * @param {string} workId - Work ID
     * @returns {Promise<Object>} Deletion confirmation
     */
    async deleteWork(orcid, workId) {
        return this._request('DELETE', `/${orcid}/works/${workId}`);
    }
    
    /**
     * Search for researchers
     * @param {string} query - Search query
     * @returns {Promise<Object>} Search results
     */
    async searchResearchers(query) {
        return this._request('GET', '/search', null, { q: query });
    }
    
    /**
     * Get researcher's affiliations
     * @param {string} orcid - ORCID ID
     * @returns {Promise<Object>} List of affiliations
     */
    async getAffiliations(orcid) {
        return this._request('GET', `/${orcid}/person`);
    }
    
    /**
     * Add an affiliation to researcher's ORCID record
     * @param {string} orcid - ORCID ID
     * @param {Object} affiliationData - Affiliation data
     * @returns {Promise<Object>} Created affiliation information
     */
    async addAffiliation(orcid, affiliationData) {
        return this._request('POST', `/${orcid}/person`, affiliationData);
    }
    
    /**
     * Create a standard work payload for ATLAS VIVO
     * @param {string} title - Work title
     * @param {string} doi - DOI of the work
     * @param {string} url - URL to the work
     * @param {string} [workType='dataset'] - Type of work
     * @param {string} [publicationDate] - Publication date (YYYY-MM-DD)
     * @returns {Object} Work payload
     */
    createWorkPayload(title, doi, url, workType = 'dataset', publicationDate = null) {
        const date = publicationDate || new Date().toISOString().split('T')[0];
        const [year, month, day] = date.split('-');
        
        return {
            title: {
                title: { value: title }
            },
            type: workType,
            url: { value: url },
            'external-ids': {
                'external-id': [
                    {
                        'external-id-type': 'doi',
                        'external-id-value': doi,
                        'external-id-url': { value: `https://doi.org/${doi}` },
                        'external-id-relationship': 'self'
                    }
                ]
            },
            'publication-date': {
                year: { value: year },
                month: { value: month },
                day: { value: day }
            }
        };
    }
    
    /**
     * Link a work to researcher's ORCID record
     * @param {string} orcid - ORCID ID
     * @param {Object} workData - Work data
     * @returns {Promise<Object>} Linking result
     */
    async linkWorkToOrcid(orcid, workData) {
        return this.addWork(orcid, workData);
    }
    
    /**
     * Link a work to multiple ORCID records
     * @param {Object} workData - Work data
     * @param {Array<string>} orcids - List of ORCID IDs
     * @returns {Promise<Object>} Linking results for all ORCIDs
     */
    async linkMultipleOrcids(workData, orcids) {
        const results = {};
        
        for (const orcid of orcids) {
            try {
                const result = await this.linkWorkToOrcid(orcid, workData);
                results[orcid] = { status: 'success', result: result };
            } catch (error) {
                results[orcid] = { status: 'error', error: error.message };
            }
        }
        
        return results;
    }
    
    /**
     * Search for ORCID by researcher name
     * @param {string} name - Researcher name
     * @returns {Promise<string|null>} ORCID ID if found, null otherwise
     */
    async getOrcidFromName(name) {
        try {
            const results = await this.searchResearchers(name);
            if (results.result && results.result.length > 0) {
                return results.result[0]['orcid-identifier']?.path || null;
            }
            return null;
        } catch (error) {
            console.error(`Error searching for ORCID: ${error.message}`);
            return null;
        }
    }
    
    /**
     * Validate ORCID format
     * @param {string} orcid - ORCID to validate
     * @returns {boolean} True if valid, false otherwise
     */
    validateOrcid(orcid) {
        const pattern = /^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$/;
        return pattern.test(orcid);
    }
    
    /**
     * Get ORCID API statistics
     * @returns {Promise<Object>} API statistics
     */
    async getStats() {
        return {
            apiVersion: 'v3.0',
            environment: this.sandbox ? 'sandbox' : 'production',
            authenticated: !!this.token,
            clientId: this.clientId ? '***REDACTED***' : null
        };
    }
}

/**
 * Factory function to create ORCID API instance
 * @param {Object} [options] - Configuration options
 * @returns {ORCIDAPI} ORCID API instance
 */
function createORCIDAPI(options = {}) {
    return new ORCIDAPI(options);
}

/**
 * Singleton instance
 */
let orcidAPIInstance = null;

/**
 * Get singleton ORCID API instance
 * @param {Object} [options] - Configuration options
 * @returns {ORCIDAPI} ORCID API instance
 */
function getORCIDAPI(options = {}) {
    if (!orcidAPIInstance) {
        orcidAPIInstance = createORCIDAPI(options);
    }
    return orcidAPIInstance;
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ORCIDAPI,
        createORCIDAPI,
        getORCIDAPI
    };
}

// Test in browser console
if (typeof window !== 'undefined') {
    window.ORCIDAPI = ORCIDAPI;
    window.createORCIDAPI = createORCIDAPI;
    window.getORCIDAPI = getORCIDAPI;
}
