# 🚀 ATLAS VIVO - Integration APIs

**Version:** 2.0.0  
**Author:** Eduardo Mauricio / Associação MILK  
**Status:** ✅ Complete and Ready for Production

---

## 📋 Overview

This directory contains **complete JavaScript API clients** for integrating ATLAS VIVO with all major platforms:

| API | File | Description | Status |
|-----|------|-------------|--------|
| **Zenodo API** | `zenodo_api_integration.js` | DOI minting, deposit management | ✅ Complete |
| **ORCID API** | `orcid_api_integration.js` | Researcher identification, work linking | ✅ Complete |
| **GitHub API** | `github_api_integration.js` | Repository management, workflows | ✅ Complete |
| **Codeberg API** | `github_api_integration.js` | Codeberg repository management | ✅ Complete |
| **Unified API** | `index.js` | Single interface for all APIs | ✅ Complete |

---

## 🎯 Features

### **Zenodo API** 📚
- ✅ Create and manage deposits
- ✅ Upload files to deposits
- ✅ Publish deposits with DOI minting
- ✅ Link deposits to ORCID records
- ✅ Search and retrieve deposit information
- ✅ Manage Zenodo communities
- ✅ Repository synchronization
- ✅ Metadata template generation

### **ORCID API** 👤
- ✅ OAuth2 authentication
- ✅ Get researcher information
- ✅ Add/Update/Delete works
- ✅ Link works to ORCID records
- ✅ Search researchers
- ✅ Manage affiliations
- ✅ Work payload creation
- ✅ Multiple ORCID linking
- ✅ ORCID validation

### **GitHub API** 🐙
- ✅ Repository management
- ✅ File operations (create, read, update, delete)
- ✅ Workflow management
- ✅ Trigger workflow runs
- ✅ Issue and PR management
- ✅ Metadata synchronization
- ✅ Cross-repository operations

### **Codeberg API** 🐙
- ✅ All GitHub API features
- ✅ Codeberg-specific endpoints
- ✅ Compatible interface

### **Unified API** 🔗
- ✅ Single interface for all platforms
- ✅ Complete deposit creation with DOI
- ✅ Automatic ORCID linking
- ✅ Multi-repository synchronization
- ✅ Unified statistics

---

## 📁 File Structure

```
agent-integration/js/
├── index.js                          # Main entry point
├── package.json                      # Node.js package configuration
├── README.md                         # This file
├── zenodo_api_integration.js        # Zenodo API client (11KB)
├── orcid_api_integration.js         # ORCID API client (12KB)
└── github_api_integration.js        # GitHub/Codeberg API client (18KB)
```

---

## 🚀 Installation

### **Node.js**

```bash
# Navigate to the js directory
cd agent-integration/js

# Install dependencies
npm install

# Or install globally
npm install -g .
```

### **Browser**

Include the scripts directly in your HTML:

```html
<!-- Include individual APIs -->
<script src="zenodo_api_integration.js"></script>
<script src="orcid_api_integration.js"></script>
<script src="github_api_integration.js"></script>

<!-- Or include the unified API -->
<script src="index.js"></script>
```

---

## 💻 Usage Examples

### **1. Initialize Individual APIs**

#### Zenodo API
```javascript
// Node.js
const { ZenodoAPI, getZenodoAPI } = require('./zenodo_api_integration.js');

// Initialize with token
const zenodo = new ZenodoAPI('your_zenodo_token');
// Or use environment variable
const zenodo = getZenodoAPI(); // Uses ZENODO_TOKEN from env

// Create a deposit
const metadata = {
    title: 'My Dataset',
    description: 'Dataset description',
    creators: [{ name: 'John Doe', affiliation: 'University' }],
    license: { id: 'CC-BY-4.0' }
};

const deposit = await zenodo.createDeposit(metadata);
console.log('Deposit created:', deposit.id);

// Publish and mint DOI
const published = await zenodo.publishDeposit(deposit.id);
console.log('DOI:', published.doi);
```

#### ORCID API
```javascript
// Node.js
const { ORCIDAPI, getORCIDAPI } = require('./orcid_api_integration.js');

// Initialize with credentials
const orcid = new ORCIDAPI({
    clientId: 'your_client_id',
    clientSecret: 'your_client_secret'
});

// Get researcher info
const researcher = await orcid.getResearcher('0009-0009-1781-4020');
console.log('Researcher:', researcher);

// Create work payload
const workPayload = orcid.createWorkPayload(
    'My Dataset',
    '10.5281/zenodo.1234567',
    'https://doi.org/10.5281/zenodo.1234567',
    'dataset'
);

// Link work to ORCID
const result = await orcid.linkWorkToOrcid('0009-0009-1781-4020', workPayload);
console.log('Work linked:', result);
```

#### GitHub API
```javascript
// Node.js
const { GitHubAPI, getGitHubAPI } = require('./github_api_integration.js');

// Initialize with token
const github = new GitHubAPI({ token: 'your_github_token' });

// List repositories
const repos = await github.listRepos('milkivc');
console.log('Repositories:', repos);

// Create/update a file
const fileResult = await github.createFile(
    'milkivc', 'atlas-datasets',
    'metadata.json',
    JSON.stringify({ title: 'Test' }, null, 2),
    'Update metadata'
);
console.log('File updated:', fileResult);

// Trigger workflow
const workflowRun = await github.triggerWorkflow(
    'milkivc', 'atlas-datasets',
    'auto-sync.yml',
    'master'
);
console.log('Workflow triggered:', workflowRun);
```

### **2. Use Unified API**

```javascript
// Node.js
const { UnifiedAPI } = require('./index.js');

// Initialize with all tokens
const api = new UnifiedAPI({
    zenodoToken: process.env.ZENODO_TOKEN,
    orcidClientId: process.env.ORCID_CLIENT_ID,
    orcidClientSecret: process.env.ORCID_CLIENT_SECRET,
    githubToken: process.env.GITHUB_TOKEN,
    codebergToken: process.env.CODEBERG_TOKEN
});

// Get all API statistics
const stats = await api.getAllStats();
console.log('API Statistics:', stats);

// Create deposit and link to ORCIDs
const result = await api.createDepositAndLink(
    {
        title: 'My Dataset',
        description: 'Dataset description',
        creators: [{ name: 'John Doe' }]
    },
    ['0009-0009-1781-4020', '0009-0007-6892-6570']
);
console.log('Complete result:', result);

// Sync all repositories
const syncResult = await api.syncAllRepositories(
    ['atlas-datasets', 'atlas-docs', 'atlas-vivo-milk'],
    {
        metadata: { title: 'Updated Metadata' },
        zenodo: { doi: '10.5281/zenodo.1234567' }
    }
);
console.log('Sync result:', syncResult);
```

### **3. Initialize All APIs at Once**

```javascript
// Node.js
const { initAllAPIs } = require('./index.js');

// Initialize all APIs with environment variables
const apis = initAllAPIs();

// Use individual APIs
const zenodoStats = await apis.zenodo.getStats();
const orcidStats = await apis.orcid.getStats();
const githubStats = await apis.github.getStats();
const codebergStats = await apis.codeberg.getStats();

console.log('All API stats:', { zenodoStats, orcidStats, githubStats, codebergStats });
```

---

## 🔐 Authentication

### **Environment Variables**

Create a `.env` file in your project root:

```bash
# Zenodo
ZENODO_TOKEN=your_zenodo_api_token
ZENODO_COMMUNITY_ID=atlas-vivo-milk

# ORCID
ORCID_CLIENT_ID=your_orcid_client_id
ORCID_CLIENT_SECRET=your_orcid_client_secret
ORCID_TOKEN=your_orcid_access_token

# GitHub
GITHUB_TOKEN=your_github_personal_access_token
REPOSITORY_OWNER=milkivc

# Codeberg
CODEBERG_TOKEN=your_codeberg_personal_access_token
CODEBERG_USERNAME=associacaomilk
```

### **Loading Environment Variables**

```javascript
// Node.js
require('dotenv').config();

// Then use the APIs
const zenodo = getZenodoAPI(); // Automatically uses ZENODO_TOKEN
const github = getGitHubAPI(); // Automatically uses GITHUB_TOKEN
```

---

## 📊 API Methods Reference

### **ZenodoAPI**

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `createDeposit(metadata, published)` | Create new deposit | metadata, published | Deposit info |
| `getDeposit(depositId)` | Get deposit info | depositId | Deposit info |
| `updateDeposit(depositId, metadata)` | Update deposit | depositId, metadata | Updated info |
| `uploadFile(depositId, file, fileName)` | Upload file | depositId, file, fileName | Upload result |
| `publishDeposit(depositId)` | Publish deposit | depositId | Published info with DOI |
| `discardDeposit(depositId)` | Discard deposit | depositId | Deletion confirmation |
| `listDeposits(page, size)` | List deposits | page, size | List of deposits |
| `searchDeposits(query, page, size)` | Search deposits | query, page, size | Search results |
| `linkToOrcid(depositId, orcid)` | Link to ORCID | depositId, orcid | Linking confirmation |
| `createDOI(metadata)` | Create DOI | metadata | DOI info |
| `getDOIInfo(doi)` | Get DOI info | doi | DOI information |
| `createMetadataTemplate(title, description, creators, license)` | Create metadata template | title, description, creators, license | Metadata template |
| `getStats()` | Get API stats | - | Statistics |

### **ORCIDAPI**

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `getResearcher(orcid)` | Get researcher info | orcid | Researcher info |
| `getResearcherWorks(orcid)` | Get researcher works | orcid | List of works |
| `getWork(orcid, workId)` | Get specific work | orcid, workId | Work info |
| `addWork(orcid, workData)` | Add work | orcid, workData | Created work |
| `updateWork(orcid, workId, workData)` | Update work | orcid, workId, workData | Updated work |
| `deleteWork(orcid, workId)` | Delete work | orcid, workId | Deletion confirmation |
| `searchResearchers(query)` | Search researchers | query | Search results |
| `getAffiliations(orcid)` | Get affiliations | orcid | List of affiliations |
| `addAffiliation(orcid, affiliationData)` | Add affiliation | orcid, affiliationData | Created affiliation |
| `createWorkPayload(title, doi, url, workType, publicationDate)` | Create work payload | title, doi, url, workType, publicationDate | Work payload |
| `linkWorkToOrcid(orcid, workData)` | Link work to ORCID | orcid, workData | Linking result |
| `linkMultipleOrcids(workData, orcids)` | Link to multiple ORCIDs | workData, orcids | Linking results |
| `getOrcidFromName(name)` | Search ORCID by name | name | ORCID ID or null |
| `validateOrcid(orcid)` | Validate ORCID format | orcid | boolean |
| `getStats()` | Get API stats | - | Statistics |

### **GitHubAPI / CodebergAPI**

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `getUser()` | Get authenticated user | - | User info |
| `getRepo(owner, repo)` | Get repository info | owner, repo | Repository info |
| `listRepos(org)` | List repositories | org | List of repos |
| `createRepo(name, description, private, autoInit)` | Create repository | name, description, private, autoInit | Created repo |
| `updateRepo(owner, repo, data)` | Update repository | owner, repo, data | Updated repo |
| `getFile(owner, repo, path)` | Get file info | owner, repo, path | File info |
| `createFile(owner, repo, path, content, message)` | Create/update file | owner, repo, path, content, message | File result |
| `deleteFile(owner, repo, path, message)` | Delete file | owner, repo, path, message | Deletion result |
| `listFiles(owner, repo, path)` | List files | owner, repo, path | List of files |
| `getWorkflow(owner, repo, workflowId)` | Get workflow info | owner, repo, workflowId | Workflow info |
| `listWorkflows(owner, repo)` | List workflows | owner, repo | List of workflows |
| `triggerWorkflow(owner, repo, workflowId, branch, inputs)` | Trigger workflow | owner, repo, workflowId, branch, inputs | Workflow run |
| `getWorkflowRuns(owner, repo, workflowId)` | Get workflow runs | owner, repo, workflowId | List of runs |
| `createIssue(owner, repo, title, body, labels)` | Create issue | owner, repo, title, body, labels | Created issue |
| `createPR(owner, repo, title, body, head, base)` | Create PR | owner, repo, title, body, head, base | Created PR |
| `syncMetadata(owner, repo, metadata)` | Sync metadata | owner, repo, metadata | Sync result |
| `getMetadata(owner, repo)` | Get all metadata | owner, repo | All metadata |
| `syncRepositories(repos, metadata)` | Sync multiple repos | repos, metadata | Sync results |
| `getStats()` | Get API stats | - | Statistics |

### **UnifiedAPI**

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `getAllStats()` | Get all API statistics | - | All statistics |
| `createDepositAndLink(metadata, orcids)` | Create deposit with DOI and link to ORCIDs | metadata, orcids | Complete result |
| `syncAllRepositories(repos, metadata)` | Sync all repositories | repos, metadata | Sync results |

---

## 📝 Examples Directory

### **Complete Workflow Example**

```javascript
// complete_workflow.js
const { UnifiedAPI } = require('./index.js');

async function completeWorkflow() {
    // Initialize API
    const api = new UnifiedAPI({
        zenodoToken: process.env.ZENODO_TOKEN,
        orcidClientId: process.env.ORCID_CLIENT_ID,
        orcidClientSecret: process.env.ORCID_CLIENT_SECRET,
        githubToken: process.env.GITHUB_TOKEN,
        codebergToken: process.env.CODEBERG_TOKEN
    });
    
    // Step 1: Create metadata
    const metadata = api.zenodo.createMetadataTemplate(
        'ATLAS VIVO Dataset',
        'Complete dataset for ATLAS VIVO project',
        [
            { name: 'Nuno', affiliation: 'Associação MILK', orcid: '0009-0009-1781-4020' },
            { name: 'Eduardo', affiliation: 'Associação MILK', orcid: '0009-0007-6892-6570' }
        ],
        'CC-BY-4.0'
    );
    
    // Step 2: Create deposit and link to ORCIDs
    const result = await api.createDepositAndLink(
        metadata,
        ['0009-0009-1781-4020', '0009-0007-6892-6570']
    );
    
    console.log('Deposit created and linked:', result);
    
    // Step 3: Sync repositories with new metadata
    const syncResult = await api.syncAllRepositories(
        ['atlas-datasets', 'atlas-docs', 'atlas-vivo-milk'],
        {
            metadata: metadata,
            zenodo: { doi: result.deposit.doi }
        }
    );
    
    console.log('Repositories synced:', syncResult);
    
    // Step 4: Get all statistics
    const stats = await api.getAllStats();
    console.log('API Statistics:', stats);
}

// Run the workflow
completeWorkflow().catch(console.error);
```

---

## 🔧 Configuration

### **Token Requirements**

| Platform | Token | Required Scopes | Where to Get |
|----------|-------|-----------------|--------------|
| **Zenodo** | `ZENODO_TOKEN` | `deposit:write`, `deposit:actions` | [Zenodo Tokens](https://zenodo.org/account/settings/applications/tokens/new/) |
| **ORCID** | `ORCID_CLIENT_ID`, `ORCID_CLIENT_SECRET` | `/read-limited`, `/activities/update`, `/person/update` | [ORCID Developer](https://orcid.org/developer-tools) |
| **GitHub** | `GITHUB_TOKEN` | `repo`, `workflow`, `read:org`, `write:org` | [GitHub Tokens](https://github.com/settings/tokens) |
| **Codeberg** | `CODEBERG_TOKEN` | `repo`, `user` | [Codeberg Applications](https://codeberg.org/user/settings/applications) |

---

## 📊 Error Handling

All APIs include comprehensive error handling:

```javascript
try {
    const deposit = await zenodo.createDeposit(metadata);
    console.log('Success:', deposit);
} catch (error) {
    console.error('Error:', error.message);
    // Handle specific error types
    if (error.message.includes('401')) {
        console.error('Authentication failed');
    } else if (error.message.includes('404')) {
        console.error('Resource not found');
    } else {
        console.error('Unknown error');
    }
}
```

---

## 🚀 Deployment

### **Node.js Application**

```javascript
// server.js
const express = require('express');
const { UnifiedAPI } = require('./agent-integration/js/index.js');

const app = express();
const port = 3000;

// Initialize API
const api = new UnifiedAPI({
    zenodoToken: process.env.ZENODO_TOKEN,
    orcidClientId: process.env.ORCID_CLIENT_ID,
    orcidClientSecret: process.env.ORCID_CLIENT_SECRET,
    githubToken: process.env.GITHUB_TOKEN,
    codebergToken: process.env.CODEBERG_TOKEN
});

// API endpoint
app.get('/api/stats', async (req, res) => {
    try {
        const stats = await api.getAllStats();
        res.json(stats);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Start server
app.listen(port, () => {
    console.log(`ATLAS VIVO API server running on port ${port}`);
});
```

### **Browser Application**

```html
<!DOCTYPE html>
<html>
<head>
    <title>ATLAS VIVO API Demo</title>
    <script src="agent-integration/js/index.js"></script>
</head>
<body>
    <h1>ATLAS VIVO API Demo</h1>
    <button onclick="testAPIs()">Test APIs</button>
    <pre id="output"></pre>
    
    <script>
        async function testAPIs() {
            try {
                // Note: Browser usage requires CORS proxy or server-side authentication
                const output = document.getElementById('output');
                output.textContent = 'Testing APIs...\n';
                
                // In browser, you would typically use a backend service
                // This is just for demonstration
                output.textContent += '✅ APIs loaded successfully!\n';
                output.textContent += 'Available APIs:\n';
                output.textContent += '  - ZenodoAPI\n';
                output.textContent += '  - ORCIDAPI\n';
                output.textContent += '  - GitHubAPI\n';
                output.textContent += '  - CodebergAPI\n';
                output.textContent += '  - UnifiedAPI\n';
                
            } catch (error) {
                console.error('Error:', error);
            }
        }
    </script>
</body>
</html>
```

---

## 📚 Documentation

### **JSDoc Comments**

All APIs include comprehensive JSDoc comments for:
- Class descriptions
- Method descriptions
- Parameter types
- Return types
- Usage examples

### **TypeScript Support**

The APIs are designed to be TypeScript-compatible. You can create type definitions:

```typescript
// types/index.d.ts
declare module 'atlas-vivo-integration-apis' {
    export class ZenodoAPI {
        constructor(token: string, sandbox?: boolean);
        createDeposit(metadata: any, published?: boolean): Promise<any>;
        // ... other methods
    }
    
    export class ORCIDAPI {
        constructor(options: { clientId: string; clientSecret: string; token?: string; sandbox?: boolean });
        getResearcher(orcid: string): Promise<any>;
        // ... other methods
    }
    
    export class GitHubAPI {
        constructor(options: { token: string; org?: string; baseUrl?: string });
        getUser(): Promise<any>;
        // ... other methods
    }
    
    export class CodebergAPI extends GitHubAPI {}
    
    export class UnifiedAPI {
        constructor(options: any);
        getAllStats(): Promise<any>;
        createDepositAndLink(metadata: any, orcids: string[]): Promise<any>;
        syncAllRepositories(repos: string[], metadata: any): Promise<any>;
    }
    
    export function initAllAPIs(): any;
}
```

---

## 🎯 Best Practices

### **1. Token Security**
- Never commit tokens to version control
- Use environment variables
- Rotate tokens regularly
- Use minimal required scopes

### **2. Error Handling**
- Always use try/catch blocks
- Handle specific error types
- Provide meaningful error messages
- Log errors for debugging

### **3. Rate Limiting**
- Respect API rate limits
- Implement retry logic for rate limits
- Use exponential backoff
- Cache responses when possible

### **4. Testing**
- Test with sandbox environments first
- Use dry-run modes when available
- Verify all tokens are valid
- Test error scenarios

---

## 📞 Support

### **Issues**
- Report issues: [GitHub Issues](https://github.com/milkivc/atlas-datasets/issues)
- Tag: `api-integration`

### **Contacts**
- **Technical Lead:** Eduardo Mauricio (eduardo@associacaomilk.pt)
- **Association:** milk@associacaomilk.pt

### **Platform Support**
- **Zenodo:** [help.zenodo.org](https://help.zenodo.org)
- **ORCID:** [support.orcid.org](https://support.orcid.org)
- **GitHub:** [support.github.com](https://support.github.com)
- **Codeberg:** [docs.codeberg.org](https://docs.codeberg.org)

---

## 📄 License

MIT License - Copyright (c) 2026 Associação MILK

---

## 🏷️ Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-06-26 | Complete JavaScript APIs created |
| 1.0.0 | 2026-06-26 | Python APIs created |

---

**Document Version:** 2.0.0  
**Last Updated:** 2026-06-26  
**Author:** Eduardo Mauricio  
**Status:** ✅ Complete - Ready for Production
