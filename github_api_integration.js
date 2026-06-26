/**
 * GitHub/Codeberg API Integration for ATLAS VIVO
 * ==============================================
 * 
 * Comprehensive JavaScript client for GitHub and Codeberg API integration.
 * Handles repository management, file operations, and workflow automation.
 * 
 * @module github_api_integration
 * @version 2.0.0
 * @author Eduardo Mauricio / Associação MILK
 */

/**
 * GitHub API Client Class
 * @class GitHubAPI
 */
class GitHubAPI {
    /**
     * Initialize GitHub API client
     * @constructor
     * @param {Object} options - Configuration options
     * @param {string} options.token - GitHub Personal Access Token
     * @param {string} [options.org='milkivc'] - Organization name
     * @param {string} [options.baseUrl='https://api.github.com'] - API base URL
     */
    constructor(options = {}) {
        this.token = options.token || process.env.GITHUB_TOKEN;
        if (!this.token) {
            throw new Error('GITHUB_TOKEN is required. Set GITHUB_TOKEN environment variable.');
        }
        
        this.org = options.org || process.env.REPOSITORY_OWNER || 'milkivc';
        this.baseUrl = options.baseUrl || 'https://api.github.com';
        
        this.headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'Authorization': `Bearer ${this.token}`
        };
    }
    
    /**
     * Make HTTP request to GitHub API
     * @private
     * @param {string} method - HTTP method (GET, POST, PUT, DELETE, PATCH)
     * @param {string} endpoint - API endpoint
     * @param {Object} [data=null] - Request body
     * @param {Object} [params=null] - Query parameters
     * @returns {Promise<Object>} API response
     */
    async _request(method, endpoint, data = null, params = null) {
        const url = new URL(endpoint, this.baseUrl);
        
        if (params) {
            Object.keys(params).forEach(key => {
                url.searchParams.append(key, params[key]);
            });
        }
        
        const options = {
            method: method.toUpperCase(),
            headers: this.headers
        };
        
        if (data && (method.toUpperCase() === 'POST' || method.toUpperCase() === 'PUT' || method.toUpperCase() === 'PATCH')) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url.toString(), options);
            
            if (!response.ok) {
                const error = await response.text();
                throw new Error(`GitHub API error: ${response.status} - ${error}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error in GitHub API request: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Get authenticated user information
     * @returns {Promise<Object>} User information
     */
    async getUser() {
        return this._request('GET', '/user');
    }
    
    /**
     * Get repository information
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @returns {Promise<Object>} Repository information
     */
    async getRepo(owner, repo) {
        return this._request('GET', `/repos/${owner}/${repo}`);
    }
    
    /**
     * List repositories
     * @param {string} [org] - Organization name (optional)
     * @returns {Promise<Array<Object>>} List of repositories
     */
    async listRepos(org = null) {
        const endpoint = org ? `/orgs/${org}/repos` : '/user/repos';
        return this._request('GET', endpoint);
    }
    
    /**
     * Create a new repository
     * @param {string} name - Repository name
     * @param {string} [description=''] - Repository description
     * @param {boolean} [private=false] - Private repository
     * @param {boolean} [autoInit=true] - Initialize with README
     * @returns {Promise<Object>} Created repository information
     */
    async createRepo(name, description = '', private = false, autoInit = true) {
        const data = {
            name: name,
            description: description,
            private: private,
            auto_init: autoInit
        };
        return this._request('POST', `/orgs/${this.org}/repos`, data);
    }
    
    /**
     * Update repository settings
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @param {Object} data - Update data
     * @returns {Promise<Object>} Updated repository information
     */
    async updateRepo(owner, repo, data) {
        return this._request('PATCH', `/repos/${owner}/${repo}`, data);
    }
    
    /**
     * Get file information
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @param {string} path - File path
     * @returns {Promise<Object>} File information
     */
    async getFile(owner, repo, path) {
        return this._request('GET', `/repos/${owner}/${repo}/contents/${path}`);
    }
    
    /**
     * Create or update a file
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @param {string} path - File path
     * @param {string} content - File content
     * @param {string} [message='Add file'] - Commit message
     * @returns {Promise<Object>} File creation result
     */
    async createFile(owner, repo, path, content, message = 'Add file') {
        // Encode content to base64
        const encodedContent = btoa(content);
        
        const data = {
            message: message,
            content: encodedContent
        };
        
        return this._request('PUT', `/repos/${owner}/${repo}/contents/${path}`, data);
    }
    
    /**
     * Delete a file
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @param {string} path - File path
     * @param {string} [message='Delete file'] - Commit message
     * @returns {Promise<Object>} File deletion result
     */
    async deleteFile(owner, repo, path, message = 'Delete file') {
        const data = {
            message: message
        };
        return this._request('DELETE', `/repos/${owner}/${repo}/contents/${path}`, data);
    }
    
    /**
     * List files in a repository
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @param {string} [path=''] - Directory path
     * @returns {Promise<Array<Object>>} List of files
     */
    async listFiles(owner, repo, path = '') {
        return this._request('GET', `/repos/${owner}/${repo}/contents/${path}`);
    }
    
    /**
     * Get workflow information
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @param {string} workflowId - Workflow ID or filename
     * @returns {Promise<Object>} Workflow information
     */
    async getWorkflow(owner, repo, workflowId) {
        return this._request('GET', `/repos/${owner}/${repo}/actions/workflows/${workflowId}`);
    }
    
    /**
     * List all workflows in a repository
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @returns {Promise<Array<Object>>} List of workflows
     */
    async listWorkflows(owner, repo) {
        return this._request('GET', `/repos/${owner}/${repo}/actions/workflows`);
    }
    
    /**
     * Trigger a workflow run
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @param {string} workflowId - Workflow ID or filename
     * @param {string} [branch='master'] - Branch to run on
     * @param {Object} [inputs={}] - Workflow inputs
     * @returns {Promise<Object>} Workflow run information
     */
    async triggerWorkflow(owner, repo, workflowId, branch = 'master', inputs = {}) {
        const data = {
            ref: branch,
            inputs: inputs
        };
        return this._request('POST', `/repos/${owner}/${repo}/actions/workflows/${workflowId}/dispatches`, data);
    }
    
    /**
     * Get workflow runs
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @param {string} [workflowId] - Workflow ID (optional)
     * @returns {Promise<Array<Object>>} List of workflow runs
     */
    async getWorkflowRuns(owner, repo, workflowId = null) {
        const endpoint = workflowId 
            ? `/repos/${owner}/${repo}/actions/workflows/${workflowId}/runs`
            : `/repos/${owner}/${repo}/actions/runs`;
        return this._request('GET', endpoint);
    }
    
    /**
     * Create a new issue
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @param {string} title - Issue title
     * @param {string} body - Issue body
     * @param {Array<string>} [labels=[]] - Issue labels
     * @returns {Promise<Object>} Created issue information
     */
    async createIssue(owner, repo, title, body, labels = []) {
        const data = {
            title: title,
            body: body,
            labels: labels
        };
        return this._request('POST', `/repos/${owner}/${repo}/issues`, data);
    }
    
    /**
     * Create a new pull request
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @param {string} title - PR title
     * @param {string} body - PR body
     * @param {string} head - Head branch
     * @param {string} [base='master'] - Base branch
     * @returns {Promise<Object>} Created PR information
     */
    async createPR(owner, repo, title, body, head, base = 'master') {
        const data = {
            title: title,
            body: body,
            head: head,
            base: base
        };
        return this._request('POST', `/repos/${owner}/${repo}/pulls`, data);
    }
    
    /**
     * Synchronize metadata files in a repository
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @param {Object} metadata - Metadata to sync
     * @returns {Promise<Object>} Sync result
     */
    async syncMetadata(owner, repo, metadata) {
        const results = {};
        
        // Update metadata.json
        if (metadata.metadata) {
            const result = await this.createFile(
                owner, repo, 'metadata.json',
                JSON.stringify(metadata.metadata, null, 2),
                'Update metadata.json'
            );
            results['metadata.json'] = result;
        }
        
        // Update .zenodo.json
        if (metadata.zenodo) {
            const result = await this.createFile(
                owner, repo, '.zenodo.json',
                JSON.stringify(metadata.zenodo, null, 2),
                'Update .zenodo.json'
            );
            results['.zenodo.json'] = result;
        }
        
        // Update CITATION.cff
        if (metadata.citation) {
            const result = await this.createFile(
                owner, repo, 'CITATION.cff',
                metadata.citation,
                'Update CITATION.cff'
            );
            results['CITATION.cff'] = result;
        }
        
        // Update codemeta.json
        if (metadata.codemeta) {
            const result = await this.createFile(
                owner, repo, 'codemeta.json',
                JSON.stringify(metadata.codemeta, null, 2),
                'Update codemeta.json'
            );
            results['codemeta.json'] = result;
        }
        
        return results;
    }
    
    /**
     * Get all metadata files from a repository
     * @param {string} owner - Repository owner
     * @param {string} repo - Repository name
     * @returns {Promise<Object>} Dictionary with all metadata
     */
    async getMetadata(owner, repo) {
        const metadata = {};
        
        // Get metadata.json
        try {
            const result = await this.getFile(owner, repo, 'metadata.json');
            if (result.content) {
                metadata.metadata = JSON.parse(atob(result.content));
            }
        } catch (error) {
            // File not found, continue
        }
        
        // Get .zenodo.json
        try {
            const result = await this.getFile(owner, repo, '.zenodo.json');
            if (result.content) {
                metadata.zenodo = JSON.parse(atob(result.content));
            }
        } catch (error) {
            // File not found, continue
        }
        
        // Get CITATION.cff
        try {
            const result = await this.getFile(owner, repo, 'CITATION.cff');
            if (result.content) {
                metadata.citation = atob(result.content);
            }
        } catch (error) {
            // File not found, continue
        }
        
        // Get codemeta.json
        try {
            const result = await this.getFile(owner, repo, 'codemeta.json');
            if (result.content) {
                metadata.codemeta = JSON.parse(atob(result.content));
            }
        } catch (error) {
            // File not found, continue
        }
        
        return metadata;
    }
    
    /**
     * Synchronize metadata across multiple repositories
     * @param {Array<string>} repos - List of repository names
     * @param {Object} metadata - Metadata to sync
     * @returns {Promise<Object>} Sync results for all repositories
     */
    async syncRepositories(repos, metadata) {
        const results = {};
        
        for (const repo of repos) {
            try {
                const result = await this.syncMetadata(this.org, repo, metadata);
                results[repo] = { status: 'success', result: result };
            } catch (error) {
                results[repo] = { status: 'error', error: error.message };
            }
        }
        
        return results;
    }
    
    /**
     * Get GitHub API statistics
     * @returns {Promise<Object>} API statistics
     */
    async getStats() {
        try {
            const user = await this.getUser();
            const repos = await this.listRepos(this.org);
            
            return {
                apiVersion: '2022-11-28',
                authenticatedUser: user.login,
                organization: this.org,
                totalRepos: repos.length,
                rateLimit: {
                    remaining: parseInt(this.headers['X-RateLimit-Remaining'] || '0'),
                    limit: parseInt(this.headers['X-RateLimit-Limit'] || '0')
                }
            };
        } catch (error) {
            return {
                error: error.message,
                organization: this.org
            };
        }
    }
}

/**
 * Codeberg API Client Class (extends GitHub API for compatibility)
 * @class CodebergAPI
 * @extends GitHubAPI
 */
class CodebergAPI extends GitHubAPI {
    /**
     * Initialize Codeberg API client
     * @constructor
     * @param {Object} options - Configuration options
     * @param {string} options.token - Codeberg Personal Access Token
     * @param {string} [options.org='associacaomilk'] - Organization name
     */
    constructor(options = {}) {
        super({
            token: options.token || process.env.CODEBERG_TOKEN,
            org: options.org || process.env.CODEBERG_USERNAME || 'associacaomilk',
            baseUrl: options.baseUrl || 'https://codeberg.org/api/v1'
        });
    }
    
    /**
     * Get Codeberg-specific statistics
     * @returns {Promise<Object>} Codeberg API statistics
     */
    async getStats() {
        try {
            const user = await this.getUser();
            const repos = await this.listRepos();
            
            return {
                apiVersion: 'v1',
                platform: 'Codeberg',
                authenticatedUser: user.login,
                organization: this.org,
                totalRepos: repos.length
            };
        } catch (error) {
            return {
                error: error.message,
                platform: 'Codeberg',
                organization: this.org
            };
        }
    }
}

/**
 * Factory function to create GitHub API instance
 * @param {Object} [options] - Configuration options
 * @returns {GitHubAPI} GitHub API instance
 */
function createGitHubAPI(options = {}) {
    return new GitHubAPI(options);
}

/**
 * Factory function to create Codeberg API instance
 * @param {Object} [options] - Configuration options
 * @returns {CodebergAPI} Codeberg API instance
 */
function createCodebergAPI(options = {}) {
    return new CodebergAPI(options);
}

/**
 * Singleton instances
 */
let githubAPIInstance = null;
let codebergAPIInstance = null;

/**
 * Get singleton GitHub API instance
 * @param {Object} [options] - Configuration options
 * @returns {GitHubAPI} GitHub API instance
 */
function getGitHubAPI(options = {}) {
    if (!githubAPIInstance) {
        githubAPIInstance = createGitHubAPI(options);
    }
    return githubAPIInstance;
}

/**
 * Get singleton Codeberg API instance
 * @param {Object} [options] - Configuration options
 * @returns {CodebergAPI} Codeberg API instance
 */
function getCodebergAPI(options = {}) {
    if (!codebergAPIInstance) {
        codebergAPIInstance = createCodebergAPI(options);
    }
    return codebergAPIInstance;
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        GitHubAPI,
        CodebergAPI,
        createGitHubAPI,
        createCodebergAPI,
        getGitHubAPI,
        getCodebergAPI
    };
}

// Test in browser console
if (typeof window !== 'undefined') {
    window.GitHubAPI = GitHubAPI;
    window.CodebergAPI = CodebergAPI;
    window.createGitHubAPI = createGitHubAPI;
    window.createCodebergAPI = createCodebergAPI;
    window.getGitHubAPI = getGitHubAPI;
    window.getCodebergAPI = getCodebergAPI;
}
