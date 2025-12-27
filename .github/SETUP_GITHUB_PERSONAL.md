# Configuración de GitHub Personal

Esta guía te ayudará a configurar este repositorio para usar tu cuenta **personal** de GitHub en lugar de la empresarial.

## Opción 1: Configuración por Repositorio (Recomendado)

### 1. Configurar Git para este repositorio específico

```bash
cd /Users/paco.ocampo/Documents/kavak/challenge/project

# Configurar usuario y email para este repositorio solamente
git config user.name "Tu Nombre Personal"
git config user.email "tu.email.personal@example.com"
```

### 2. Verificar la configuración

```bash
git config --local user.name
git config --local user.email
```

### 3. Configurar el remote de GitHub

```bash
# Si ya existe un remote, elimínalo primero
git remote remove origin 2>/dev/null || true

# Agrega tu repositorio personal de GitHub
git remote add origin https://github.com/TU_USUARIO_PERSONAL/nombre-del-repo.git

# O si prefieres usar SSH (más seguro)
git remote add origin git@github.com-personal:TU_USUARIO_PERSONAL/nombre-del-repo.git
```

### 4. Configurar autenticación

#### Opción A: Personal Access Token (HTTPS)

1. Ve a GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Genera un nuevo token con permisos: `repo`, `workflow`, `write:packages`
3. Guarda el token de forma segura

```bash
# Git te pedirá el token cuando hagas push
git push -u origin main
```

#### Opción B: SSH Key (Recomendado)

1. **Generar una nueva SSH key para tu cuenta personal** (si no tienes una):

```bash
# Generar SSH key específica para GitHub personal
ssh-keygen -t ed25519 -C "tu.email.personal@example.com" -f ~/.ssh/id_ed25519_github_personal

# Agregar al ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_github_personal
```

2. **Agregar la clave pública a GitHub**:

```bash
# Copiar la clave pública
cat ~/.ssh/id_ed25519_github_personal.pub
# Luego ve a GitHub → Settings → SSH and GPG keys → New SSH key
```

3. **Configurar SSH para usar la clave correcta**:

Crea o edita `~/.ssh/config`:

```
# GitHub Personal
Host github.com-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github_personal
    IdentitiesOnly yes

# GitHub Empresarial (si la necesitas)
Host github.com-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github_work
    IdentitiesOnly yes
```

4. **Usar el host personalizado en el remote**:

```bash
git remote set-url origin git@github.com-personal:TU_USUARIO_PERSONAL/nombre-del-repo.git
```

## Opción 2: Usar GitHub CLI (gh)

Si tienes `gh` instalado, puedes autenticarte fácilmente:

```bash
# Autenticar con tu cuenta personal
gh auth login

# Seleccionar GitHub.com
# Seleccionar HTTPS o SSH
# Seleccionar tu cuenta personal
# Autenticar con navegador o token

# Crear el repositorio y configurar el remote
gh repo create nombre-del-repo --private --source=. --remote=origin --push
```

## Verificar la Configuración

```bash
# Verificar usuario y email
git config --local user.name
git config --local user.email

# Verificar remote
git remote -v

# Probar conexión (si usas SSH)
ssh -T git@github.com-personal

# O probar con HTTPS
git ls-remote origin
```

## Actualizar CODEOWNERS

Edita `.github/CODEOWNERS` y reemplaza `@paco.ocampo` con tu usuario personal de GitHub:

```
* @TU_USUARIO_PERSONAL
```

## Troubleshooting

### Error: "Permission denied (publickey)"
- Verifica que tu SSH key esté agregada a GitHub
- Verifica que estés usando el host correcto en `~/.ssh/config`
- Prueba: `ssh -T git@github.com-personal`

### Error: "Authentication failed"
- Si usas HTTPS, verifica que tu token tenga los permisos correctos
- Si usas SSH, verifica que la clave esté en el ssh-agent: `ssh-add -l`

### Cambiar entre cuentas
Si necesitas cambiar entre cuenta personal y empresarial:

```bash
# Para este repositorio (personal)
git config --local user.email "personal@example.com"

# Para otro repositorio (empresarial)
cd /ruta/al/repo/empresarial
git config --local user.email "empresarial@example.com"
```

## Script de Configuración Rápida

Ejecuta el script `setup-github-personal.sh` que está en la raíz del proyecto para automatizar estos pasos.

