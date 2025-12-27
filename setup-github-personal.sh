#!/bin/bash

# Script para configurar el repositorio con cuenta personal de GitHub
# Uso: ./setup-github-personal.sh

set -e

echo "🔧 Configuración de GitHub Personal"
echo "===================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que estamos en un repositorio Git
if [ ! -d .git ]; then
    echo -e "${RED}❌ Error: Este directorio no es un repositorio Git${NC}"
    echo "Ejecuta 'git init' primero si quieres inicializar uno nuevo."
    exit 1
fi

# 1. Configurar usuario y email
echo -e "${YELLOW}📝 Paso 1: Configurar usuario y email${NC}"
read -p "Ingresa tu nombre completo: " GIT_NAME
read -p "Ingresa tu email personal de GitHub: " GIT_EMAIL

git config user.name "$GIT_NAME"
git config user.email "$GIT_EMAIL"

echo -e "${GREEN}✅ Usuario configurado: $GIT_NAME <$GIT_EMAIL>${NC}"
echo ""

# 2. Configurar remote
echo -e "${YELLOW}🔗 Paso 2: Configurar remote de GitHub${NC}"
read -p "Ingresa tu usuario de GitHub personal: " GITHUB_USER
read -p "Ingresa el nombre del repositorio (o presiona Enter para usar 'kavak-agent'): " REPO_NAME
REPO_NAME=${REPO_NAME:-kavak-agent}

echo ""
echo "Selecciona el método de autenticación:"
echo "1) HTTPS (Personal Access Token)"
echo "2) SSH (Recomendado)"
read -p "Opción [1 o 2]: " AUTH_METHOD

if [ "$AUTH_METHOD" = "2" ]; then
    # SSH
    REMOTE_URL="git@github.com-personal:${GITHUB_USER}/${REPO_NAME}.git"
    
    echo ""
    echo -e "${YELLOW}🔑 Verificando configuración SSH...${NC}"
    
    # Verificar si existe ~/.ssh/config
    if [ ! -f ~/.ssh/config ]; then
        echo -e "${YELLOW}⚠️  No se encontró ~/.ssh/config${NC}"
        echo "¿Quieres crear una configuración SSH para GitHub personal? (s/n)"
        read -p "> " CREATE_SSH_CONFIG
        
        if [ "$CREATE_SSH_CONFIG" = "s" ] || [ "$CREATE_SSH_CONFIG" = "S" ]; then
            SSH_KEY_PATH="$HOME/.ssh/id_ed25519_github_personal"
            
            # Verificar si la clave ya existe
            if [ ! -f "$SSH_KEY_PATH" ]; then
                echo "Generando nueva SSH key..."
                ssh-keygen -t ed25519 -C "$GIT_EMAIL" -f "$SSH_KEY_PATH" -N ""
                echo -e "${GREEN}✅ SSH key generada en $SSH_KEY_PATH${NC}"
            fi
            
            # Agregar configuración a ~/.ssh/config
            mkdir -p ~/.ssh
            cat >> ~/.ssh/config << EOF

# GitHub Personal
Host github.com-personal
    HostName github.com
    User git
    IdentityFile $SSH_KEY_PATH
    IdentitiesOnly yes
EOF
            echo -e "${GREEN}✅ Configuración SSH agregada${NC}"
            
            # Agregar al ssh-agent
            eval "$(ssh-agent -s)" > /dev/null 2>&1
            ssh-add "$SSH_KEY_PATH" 2>/dev/null || true
            
            echo ""
            echo -e "${YELLOW}📋 IMPORTANTE: Agrega esta clave pública a GitHub:${NC}"
            echo "1. Ve a: https://github.com/settings/keys"
            echo "2. Click en 'New SSH key'"
            echo "3. Copia el contenido de: $SSH_KEY_PATH.pub"
            echo ""
            cat "$SSH_KEY_PATH.pub"
            echo ""
            read -p "Presiona Enter cuando hayas agregado la clave a GitHub..."
        fi
    else
        echo -e "${GREEN}✅ ~/.ssh/config encontrado${NC}"
    fi
    
    # Probar conexión SSH
    echo "Probando conexión SSH..."
    if ssh -T git@github.com-personal 2>&1 | grep -q "successfully authenticated"; then
        echo -e "${GREEN}✅ Conexión SSH exitosa${NC}"
    else
        echo -e "${YELLOW}⚠️  No se pudo verificar la conexión SSH automáticamente${NC}"
        echo "Asegúrate de que tu SSH key esté agregada a GitHub"
    fi
else
    # HTTPS
    REMOTE_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
    echo -e "${YELLOW}⚠️  Recuerda que necesitarás un Personal Access Token para hacer push${NC}"
    echo "Genera uno en: https://github.com/settings/tokens"
fi

# Eliminar remote existente si hay uno
if git remote get-url origin > /dev/null 2>&1; then
    echo ""
    echo "Remote 'origin' ya existe:"
    git remote -v
    read -p "¿Reemplazar el remote existente? (s/n): " REPLACE_REMOTE
    if [ "$REPLACE_REMOTE" = "s" ] || [ "$REPLACE_REMOTE" = "S" ]; then
        git remote remove origin
        echo -e "${GREEN}✅ Remote anterior eliminado${NC}"
    else
        echo "Manteniendo remote existente. Puedes cambiarlo manualmente con:"
        echo "  git remote set-url origin $REMOTE_URL"
        exit 0
    fi
fi

# Agregar nuevo remote
git remote add origin "$REMOTE_URL"
echo -e "${GREEN}✅ Remote configurado: $REMOTE_URL${NC}"
echo ""

# 3. Verificar configuración
echo -e "${YELLOW}🔍 Verificando configuración...${NC}"
echo ""
echo "Usuario Git:"
git config user.name
git config user.email
echo ""
echo "Remote:"
git remote -v
echo ""

# 4. Actualizar CODEOWNERS
if [ -f .github/CODEOWNERS ]; then
    echo -e "${YELLOW}📝 Actualizando CODEOWNERS...${NC}"
    # Reemplazar @paco.ocampo con el usuario de GitHub
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/@paco\.ocampo/@${GITHUB_USER}/g" .github/CODEOWNERS
    else
        # Linux
        sed -i "s/@paco\.ocampo/@${GITHUB_USER}/g" .github/CODEOWNERS
    fi
    echo -e "${GREEN}✅ CODEOWNERS actualizado${NC}"
fi

echo ""
echo -e "${GREEN}✅ Configuración completada!${NC}"
echo ""
echo "Próximos pasos:"
echo "1. Si usas SSH, asegúrate de haber agregado tu clave pública a GitHub"
echo "2. Crea el repositorio en GitHub si no existe:"
echo "   https://github.com/new"
echo "3. Haz tu primer push:"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo "   git push -u origin main"
echo ""

