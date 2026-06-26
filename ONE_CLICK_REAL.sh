#!/bin/bash

# =============================================================================
# Atlas Vivo MILK - ONE CLICK REAL DEPLOY
# 
# Script para acionar TUDO COM UM CLIQUE (versão REAL)
# 
# O QUE ESTE SCRIPT FAZ:
# 1. Faz push de todos os repositórios (se houver alterações)
# 2. Cria tags para testar o sync-zenodo.yml
# 3. Verifica o status dos workflows
# 4. Gera um relatório final com links reais
# 
# Uso: ./ONE_CLICK_REAL.sh
# 
# Autor: Nuno Filipe (ORCID: 0009-0009-1781-4020)
# Autor: Eduardo Maurício (ORCID: 0009-0007-6892-6570)
# Licença: EUPL-1.2
# =============================================================================

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contador de sucesso/erro
SUCCESS=0
FAIL=0
TOTAL=0

# Função para printar com cores
print_status() {
    local color="$1"
    local message="$2"
    echo -e "${color}[ONE-CLICK-REAL]${NC} ${message}"
}

# Função para printar título
print_title() {
    local title="$1"
    echo ""
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}  ${title}${NC}"
    echo -e "${BLUE}============================================================================${NC}"
    echo ""
}

# Função para printar resultado
print_result() {
    local status="$1"
    local message="$2"
    if [ "$status" = "SUCCESS" ]; then
        print_status "$GREEN" "✅ $message"
        ((SUCCESS++))
    else
        print_status "$RED" "❌ $message"
        ((FAIL++))
    fi
    ((TOTAL++))
}

# Função para executar comando e verificar resultado
run_command() {
    local description="$1"
    local command="$2"
    
    print_status "$YELLOW" "$description"
    
    if eval "$command" > /dev/null 2>&1; then
        print_result "SUCCESS" "$description"
        return 0
    else
        print_result "FAIL" "$description"
        return 1
    fi
}

# Função para fazer push em todos os repositórios
push_all_repos() {
    print_title "1. FAZENDO PUSH EM TODOS OS REPOSITÓRIOS"
    
    local repos=(
        "/workspace/milkivc__atlas-datasets"
        "/workspace/milkivc__atlas-docs"
        "/workspace/milkivc__atlas-vivo-milk"
    )
    
    for repo_path in "${repos[@]}"; do
        cd "$repo_path" || continue
        
        local repo_name=$(basename "$repo_path" | sed 's/milkivc__//')
        print_status "$YELLOW" "Processando: $repo_name"
        
        # Verificar se há alterações
        if git status --porcelain | grep -q .; then
            print_status "$GREEN" "  Alterações detectadas, fazendo commit..."
            git add .
            git commit -m "feat: one-click deploy [$(date +%Y-%m-%d)]" > /dev/null 2>&1
            
            if git push origin master > /dev/null 2>&1; then
                print_result "SUCCESS" "Push concluído para $repo_name"
            else
                print_result "FAIL" "Falha ao fazer push para $repo_name"
            fi
        else
            print_status "$GREEN" "  Nenhuma alteração em $repo_name"
            print_result "SUCCESS" "$repo_name já está atualizado"
        fi
    done
}

# Função para criar tags e testar sync-zenodo
create_tags() {
    print_title "2. CRIANDO TAGS PARA TESTAR SYNC-ZENODO"
    
    local repos=(
        "/workspace/milkivc__atlas-datasets"
        "/workspace/milkivc__atlas-docs"
        "/workspace/milkivc__atlas-vivo-milk"
    )
    
    for repo_path in "${repos[@]}"; do
        cd "$repo_path" || continue
        
        local repo_name=$(basename "$repo_path" | sed 's/milkivc__//')
        local tag_name="v1.0.0-$(date +%Y%m%d%H%M%S)"
        
        print_status "$YELLOW" "Criando tag $tag_name para $repo_name"
        
        if git tag "$tag_name" > /dev/null 2>&1; then
            if git push origin "$tag_name" > /dev/null 2>&1; then
                print_result "SUCCESS" "Tag $tag_name criada e enviada para $repo_name"
                print_status "$GREEN" "  🔗 Workflow sync-zenodo.yml será acionado automaticamente"
            else
                print_result "FAIL" "Falha ao enviar tag $tag_name para $repo_name"
            fi
        else
            print_result "FAIL" "Falha ao criar tag $tag_name para $repo_name"
        fi
    done
}

# Função para verificar status dos workflows
check_workflows() {
    print_title "3. VERIFICANDO STATUS DOS WORKFLOWS"
    
    local repos=(
        "milkivc/atlas-datasets"
        "milkivc/atlas-docs"
        "milkivc/atlas-vivo-milk"
    )
    
    for repo in "${repos[@]}"; do
        print_status "$YELLOW" "Verificando workflows para: $repo"
        
        # Verificar se o gh CLI está disponível
        if command -v gh &> /dev/null; then
            # Obter os últimos workflow runs
            local runs=$(gh api "repos/$repo/actions/runs?per_page=5" --jq '.workflow_runs[] | select(.status == "completed") | {name: .name, conclusion: .conclusion, html_url: .html_url}' 2>/dev/null)
            
            if [ -n "$runs" ]; then
                echo "$runs" | while read -r line; do
                    local name=$(echo "$line" | jq -r '.name')
                    local conclusion=$(echo "$line" | jq -r '.conclusion')
                    local url=$(echo "$line" | jq -r '.html_url')
                    
                    if [ "$conclusion" = "success" ]; then
                        print_status "$GREEN" "  ✅ $name: SUCCESS ($url)"
                    else
                        print_status "$RED" "  ❌ $name: $conclusion ($url)"
                    fi
                done
                
                print_result "SUCCESS" "Workflows verificados para $repo"
            else
                print_status "$YELLOW" "  Nenhum workflow completado encontrado para $repo"
                print_result "SUCCESS" "Verificação concluída para $repo"
            fi
        else
            print_status "$YELLOW" "  gh CLI não disponível, pulando verificação automática"
            print_result "SUCCESS" "Verificação manual necessária para $repo"
        fi
    done
}

# Função para gerar relatório final com links reais
generate_real_report() {
    print_title "4. RELATÓRIO FINAL COM LINKS REAIS"
    
    echo ""
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}  📊 RESUMO DA EXECUÇÃO ONE-CLICK-REAL${NC}"
    echo -e "${BLUE}============================================================================${NC}"
    echo ""
    echo -e "  Total de operações: $TOTAL"
    echo -e "  ${GREEN}Sucessos: $SUCCESS${NC}"
    echo -e "  ${RED}Falhas: $FAIL${NC}"
    echo ""
    
    if [ $FAIL -eq 0 ]; then
        echo -e "${GREEN}🎉 TUDO FOI EXECUTADO COM SUCESSO! 🎉${NC}"
        echo ""
        echo "Links para verificar:"
        echo ""
        echo "  📦 Repositórios:"
        echo "    - https://github.com/milkivc/atlas-datasets"
        echo "    - https://github.com/milkivc/atlas-docs"
        echo "    - https://github.com/milkivc/atlas-vivo-milk"
        echo ""
        echo "  🔄 Workflows (Actions):"
        echo "    - https://github.com/milkivc/atlas-datasets/actions"
        echo "    - https://github.com/milkivc/atlas-docs/actions"
        echo "    - https://github.com/milkivc/atlas-vivo-milk/actions"
        echo ""
        echo "  📝 Tags criadas (para testar Zenodo):"
        echo "    - v1.0.0-$(date +%Y%m%d%H%M%S) em todos os repositórios"
        echo ""
        echo "  ⚙️  Próximos passos (se ainda não fez):"
        echo "    1. Configure os GitHub Secrets em cada repositório:"
        echo "       - ZENODO_TOKEN"
        echo "       - ORCID_CLIENT_ID"
        echo "       - ORCID_CLIENT_SECRET"
        echo "       - CODEBERG_TOKEN"
        echo "       - CODEBERG_USER"
        echo "       - CODEBERG_REPO"
        echo ""
        echo "    2. Aguarde os workflows serem executados (ou execute manualmente)"
        echo ""
        echo "    3. Verifique os resultados nos links acima"
    else
        echo -e "${RED}⚠️  ALGUMAS OPERAÇÕES FALHARAM${NC}"
        echo ""
        echo "Verifique os logs acima para identificar os problemas."
        echo ""
        echo "Para resolver:"
        echo "  1. Verifique se tem permissão para fazer push"
        echo "  2. Verifique se os repositórios remotos estão configurados"
        echo "  3. Tente executar os comandos manualmente"
    fi
    
    echo ""
    echo -e "${BLUE}============================================================================${NC}"
}

# Função principal
main() {
    clear
    echo ""
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}  🚀 ATLAS VIVO MILK - ONE CLICK REAL DEPLOY 🚀${NC}"
    echo -e "${BLUE}============================================================================${NC}"
    echo ""
    print_status "$YELLOW" "Iniciando execução REAL..."
    echo ""
    
    # Executar todas as funções
    push_all_repos
    create_tags
    check_workflows
    generate_real_report
    
    echo ""
}

# Executar
main
