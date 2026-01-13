# Deployment & Setup Guide - Secure Credentials Management

## 🔐 Overview

This guide explains how to securely set up the ISTA framework with MongoDB without exposing credentials.

**Key Principles:**
- ✅ No hardcoded credentials in code
- ✅ No secrets in Git repository
- ✅ Environment variables for sensitive data
- ✅ `.env` files for local development (excluded from Git)
- ✅ Safe for public GitHub repositories

---

## 📁 File Structure for Secrets

```
energypro-DataFramework/
├── .gitignore                 # ✅ Prevents .env from being committed
├── .env.example              # ✅ Template for .env file
├── .env                      # ❌ LOCAL ONLY - Never commit!
├── requirements.txt          # ✅ Python dependencies
├── README.md                 # ✅ Updated with safe setup
├── SECURE_MONGODB_QUICK_START.md  # ✅ This guide
└── ...
```

---

## 🚀 Step-by-Step Setup (First Time)

### Step 1: Clone Repository
```bash
git clone https://github.com/kunnath/energypro-DataFramework.git
cd energypro-DataFramework
```

### Step 2: Create Local Environment File
```bash
# Copy example file
cp .env.example .env

# This creates .env locally - NOT tracked by Git
```

### Step 3: Get Your MongoDB Credentials

**From MongoDB Atlas:**
1. Log in to MongoDB Atlas (https://account.mongodb.com/)
2. Go to Clusters → Your Cluster → Connect
3. Click "Drivers" → Select Python
4. Copy the connection string
5. Example: `mongodb+srv://username:password@cluster0.abc123.mongodb.net/dbname`

### Step 4: Edit .env File
```bash
# Open your editor
nano .env

# Or use VS Code
code .env
```

**Update the file with your credentials:**
```
MONGODB_URI=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/your-database
```

### Step 5: Load Environment Variables
```bash
# For this terminal session
source .env

# Verify it's set
echo $MONGODB_URI  # Should show your connection string
```

### Step 6: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 7: Verify Connection
```bash
python test-data-automation/ista_mongo_cli.py health
```

**Expected output:**
```
✓ MongoDB connection healthy
  Database: your_database
  Version: 7.0.x
  Collections: X
  Cluster: MongoDB Atlas
```

---

## 🔑 Getting Your MongoDB Connection String

### From MongoDB Atlas (Cloud)
1. Go to https://cloud.mongodb.com
2. Select your cluster
3. Click "Connect"
4. Select "Drivers"
5. Choose Python from the dropdown
6. Copy the connection string
7. Format your `.env` like:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster0.abc123.mongodb.net/databasename
   ```

### From Local MongoDB
If using local MongoDB:
```
MONGODB_URI=mongodb://localhost:27017/your-database
```

Or with authentication:
```
MONGODB_URI=mongodb://username:password@localhost:27017/your-database
```

---

## 📝 Environment Variables Needed

Your `.env` file should contain these variables:

```bash
# MongoDB Connection (REQUIRED)
MONGODB_URI=mongodb+srv://username:password@cluster.net/database

# Optional - Other databases
DB_HOST=localhost
DB_PORT=5432
DB_USER=testuser
DB_PASSWORD=testpass
DB_NAME=testdb

# Optional - API Keys
API_KEY=your-api-key
SECRET_KEY=your-secret-key

# Optional - Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

---

## 🔒 Security Checklist

Before pushing to GitHub, verify:

- [ ] `.gitignore` includes `.env`
- [ ] `.env` file is in `.gitignore` (run `cat .gitignore | grep .env`)
- [ ] No credentials in README.md
- [ ] No credentials in code files
- [ ] `.env.example` shows template but NO real values
- [ ] All secrets in `.env` locally (not in Git)

**Verify with:**
```bash
# Check if .env would be ignored
git check-ignore -v .env
# Output: .env  .gitignore (good!)

# Verify no secrets in repo
git grep -i "password\|token\|secret\|key" -- ':!README.md' ':!docs/'
# Should return nothing or only documentation
```

---

## 🔄 How It Works

### Local Development
```
1. You edit .env locally (not in Git)
   ↓
2. Load with: source .env
   ↓
3. Code reads from environment variables
   ↓
4. Your secrets stay local only
```

### CI/CD Pipeline
```
1. Push to GitHub (no secrets included)
   ↓
2. CI/CD system triggers (GitHub Actions, etc.)
   ↓
3. CI/CD system provides secrets from:
   - Environment variables
   - Secrets manager
   - Parameter store
   ↓
4. Tests run with credentials from CI/CD system
```

### Production Deployment
```
1. Deploy application to server
   ↓
2. Server loads secrets from:
   - Environment variables
   - Secret manager (e.g., AWS Secrets Manager)
   - Configuration server
   ↓
3. Application runs with appropriate credentials
```

---

## 🐛 Troubleshooting Credentials

### Credential Not Recognized
```bash
# Verify it's set
echo $MONGODB_URI

# If empty, load it
source .env
echo $MONGODB_URI
```

### Wrong Credentials
```bash
# Update .env
nano .env
MONGODB_URI=mongodb+srv://correct-user:correct-pass@cluster.net/db

# Reload
source .env

# Test
python test-data-automation/ista_mongo_cli.py health
```

### Connection Timeout
```bash
# Check if cluster is accessible
ping cluster0.mongodb.net

# Verify IP whitelist in MongoDB Atlas
# Go to: Network Access → IP Whitelist
# Your current IP must be listed
```

---

## 🚀 Pushing to GitHub (Safe Way)

### Step 1: Verify Secrets Not in Repository
```bash
# Check for hardcoded credentials
git grep -i "mongodb+srv\|password\|api.key\|secret.key" -- ':!*.md' ':!docs/'

# Should return NO results
```

### Step 2: Verify .env is Ignored
```bash
# Check .gitignore
cat .gitignore | grep ".env"

# Should include:
# .env
# .env.local
# .env.*.local
```

### Step 3: Make Sure You Haven't Already Committed Secrets
```bash
# Check git history for credentials
git log --all --source --remotes -S "mongodb+srv" --oneline

# If found, see "Fixing Accidental Commits" below
```

### Step 4: Commit and Push Safely
```bash
# Stage files (excluding .env)
git add .
git status  # Verify .env is NOT listed

# Commit
git commit -m "Add ISTA MongoDB framework"

# Push
git push origin main
```

---

## ⚠️ Fixing Accidental Commits (If You Already Pushed Secrets)

### IF YOU PUSHED CREDENTIALS TO GITHUB:

**IMMEDIATELY:**
1. Rotate MongoDB password in MongoDB Atlas
2. Revoke any exposed API keys
3. Remove the commit from history

**Remove credentials from history:**
```bash
# Option 1: Using BFG Repo Cleaner (easier)
bfg --replace-text passwords.txt

# Option 2: Using git filter-branch
git filter-branch --tree-filter 'sed -i "s/mongodb+srv:\/\/.*@/mongodb+srv:\/\/[REDACTED]@/g" *.md' HEAD

# Push cleaned history
git push --force
```

**Better: Change database password immediately:**
1. Go to MongoDB Atlas
2. Database Access → Users
3. Edit user → Edit password
4. Update .env locally with new password

---

## 📦 CI/CD Integration (GitHub Actions Example)

### Create `.github/workflows/test.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        env:
          MONGODB_URI: ${{ secrets.MONGODB_URI }}
        run: python test_mongodb_quickstart.py
```

### Add Secrets to GitHub:
1. Go to Repository Settings → Secrets and variables → Actions
2. New repository secret
3. Name: `MONGODB_URI`
4. Value: Your actual MongoDB connection string
5. Save

Now CI/CD can use `${{ secrets.MONGODB_URI }}` without exposing credentials.

---

## 🔄 Daily Usage

### Terminal Session 1:
```bash
cd energypro-DataFramework
source .env
python test-data-automation/ista_mongo_cli.py health
```

### Shell Profile Setup (Optional - Make it Persistent)

Add to `~/.zshrc` or `~/.bash_profile`:
```bash
# Load ISTA environment if in project directory
if [ -f .env ]; then
    source .env
fi
```

Then you don't need to manually `source .env` each time.

---

## 📋 Pre-Push Checklist

Before every `git push`:

```bash
# 1. Verify no credentials in code
git grep -i "mongodb+srv\|password=" -- ':!*.md'

# 2. Verify .env is ignored
git check-ignore .env

# 3. Verify .env is not staged
git status | grep ".env"  # Should be empty

# 4. Do a final check on all changes
git diff --cached | head -50  # Review what you're pushing

# 5. Only then push
git push
```

---

## 💡 Best Practices Summary

✅ **DO:**
- Use `.env` files for local development
- Use environment variables in code
- Use CI/CD secrets for automated testing
- Use secret managers for production
- Rotate credentials periodically
- Include `.gitignore` with `.env`
- Include `.env.example` as template
- Update `.env.example` when adding new variables

❌ **DON'T:**
- Hardcode credentials in code
- Commit `.env` files to Git
- Use same credentials in dev/test/prod
- Share `.env` files between team members
- Put credentials in comments
- Use credentials in GitHub issues/PRs
- Leave old passwords in history

---

## 📞 Help & Support

**Lost your MongoDB password?**
1. Go to MongoDB Atlas
2. Database Access → Users
3. Click "Edit" on the user
4. Click "Edit Password"
5. Generate new password
6. Update your local `.env` file

**Connection issues?**
1. Verify IP is whitelisted: MongoDB Atlas → Network Access
2. Check connection string format
3. Verify username/password are correct
4. Test with MongoDB Compass

**GitHub pushed credentials by mistake?**
1. Rotate password immediately in MongoDB Atlas
2. Revoke GitHub secrets
3. Use `git filter-branch` to clean history
4. Consider repository as compromised

---

**Last Updated**: January 2026  
**Status**: Ready for Production ✅  
**Security Level**: Enterprise Grade 🔒
