# ISTA MongoDB Quick Start Guide - SAFE VERSION

## 📦 Your MongoDB Setup

To use this framework, you need:
- MongoDB Atlas cluster (or local MongoDB instance)
- Your connection string (get from MongoDB Atlas dashboard)
- Database credentials (username and password)

**To Get Your Connection String:**
1. Go to MongoDB Atlas → Clusters → Connect
2. Select "Drivers" → Python
3. Copy the connection string
4. Format: `mongodb+srv://username:password@cluster.mongodb.net/database`

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone Repository
```bash
git clone https://github.com/kunnath/energypro-DataFramework.git
cd energypro-DataFramework
```

### Step 2: Set Up Environment File
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials
nano .env
# Or use your preferred editor
```

**Your .env file should contain:**
```
MONGODB_URI=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/your-database
```

⚠️ **IMPORTANT**: Never commit `.env` file to Git! It's in `.gitignore` for security.

### Step 3: Install Dependencies
```bash
source .env
pip install -r requirements.txt
```

### Step 4: Verify Connection
```bash
python test-data-automation/ista_mongo_cli.py health
```

Expected output:
```
✓ MongoDB connection healthy
  Database: your_database
  Version: 7.0.x or higher
  Collections: X
  Cluster: MongoDB Atlas
```

### Step 5: Provision Test Data
```bash
# Provision specific collections
python test-data-automation/ista_mongo_cli.py provision \
  -d movies \
  -d users \
  --volumes '{"movies":100,"users":50}'
```

### Step 6: Check Collection Status
```bash
python test-data-automation/ista_mongo_cli.py status
```

### Step 7: View Sample Documents
```bash
python test-data-automation/ista_mongo_cli.py show -c movies --limit 5
```

### Step 8: Run Quick Start Tests
```bash
python test_mongodb_quickstart.py
```

Expected: All 5 tests should pass ✅

---

## 📊 CLI Commands Reference

### Health Check
```bash
python test-data-automation/ista_mongo_cli.py health
```
Verify MongoDB connection and display cluster info.

### Show Status
```bash
python test-data-automation/ista_mongo_cli.py status
```
Display collection statistics (document count, size, indexes).

### Provision Test Data
```bash
python test-data-automation/ista_mongo_cli.py provision -d movies --volumes '{"movies":100}'
```
Insert synthetic test data into collections.

Options:
- `-d` / `--datasets`: Collection names to provision
- `--volumes`: JSON dict with document counts per collection
- `--batch-size`: Documents per batch (default: 1000)

### Show Sample Documents
```bash
python test-data-automation/ista_mongo_cli.py show -c movies --limit 5
```
Display sample documents from a collection.

### Cleanup Data
```bash
python test-data-automation/ista_mongo_cli.py cleanup -c movies --force
```
Delete test data from collections.

---

## 🏗️ Data Factory Usage

Generate realistic synthetic test data programmatically:

```python
from test_data_automation.mongo_factories import MovieFactory, UserFactory

# Single document
movie = MovieFactory.create()
user = UserFactory.create()

# Batch creation
movies = MovieFactory.create_batch(100)
users = UserFactory.create_batch(50)

# With custom values
movie = MovieFactory.create(year=2024, rated='PG-13')
user = UserFactory.create(email='custom@example.com')

# Variant factories
classic_movie = MovieFactory.create_classic_movie()  # Pre-1980
premium_user = UserFactory.create_premium_user()     # Premium subscription
```

---

## 🧪 Writing Tests with Factories

```python
from test_data_automation.mongo_factories import MovieFactory, UserFactory

def test_movie_search():
    """Test movie search functionality"""
    # Generate realistic test data
    movies = MovieFactory.create_batch(10)
    
    # Your test logic here
    assert len(movies) > 0
    assert all('title' in m for m in movies)
    
    print(f"✓ Test passed with {len(movies)} movies")
```

---

## 🔄 Using the Data Adapter for Multiple Databases

The DataAdapter allows you to switch between databases without code changes:

```python
from governance.data_adapter import get_adapter

# MongoDB
mongo_adapter = get_adapter('mongodb')
mongo_adapter.connect('mongodb+srv://user:pass@cluster.net/db')
docs = mongo_adapter.find_documents('movies', {'year': {'$gte': 2020}})
mongo_adapter.disconnect()

# PostgreSQL (when implemented)
pg_adapter = get_adapter('postgresql')
pg_adapter.connect('postgresql://user:pass@localhost/testdb')
rows = pg_adapter.find_documents('movies', {'year': {'$gte': 2020}})
pg_adapter.disconnect()
```

---

## 🆘 Troubleshooting

### "MONGODB_URI environment variable not set"
**Solution:**
```bash
# Option 1: Load from .env file
source .env

# Option 2: Set directly
export MONGODB_URI="mongodb+srv://user:pass@cluster.net/db"
```

### "Connection refused" or "Network timeout"
**Solutions:**
1. Verify your MongoDB cluster is running
2. Check your connection string is correct
3. Ensure your IP is whitelisted in MongoDB Atlas (Network Access → IP Whitelist)
4. Check network connectivity: `ping cluster0.mongodb.net`

### "Authentication failed"
**Solutions:**
1. Verify username and password in connection string
2. Check credentials in MongoDB Atlas
3. Ensure user has access to the specific database
4. Try resetting the password in MongoDB Atlas

### "Collection not found"
**Solutions:**
1. Verify collection names in your provision commands
2. Check that provision command completed successfully
3. View all collections: `ista status`

### Slow Data Provisioning
**Solutions:**
1. Reduce batch size: `--batch-size 100` (default: 1000)
2. Reduce volume: `--volumes '{"movies":10}'` instead of 1000
3. Check network latency to MongoDB Atlas cluster

---

## 📚 Additional Documentation

| Document | Purpose |
|----------|---------|
| **README.md** | Framework overview |
| **INDEX.md** | Navigation and learning paths |
| **ARCHITECTURE_DIAGRAMS.md** | Visual system overview |
| **docs/07_MONGODB_ADAPTATION.md** | Technical deep dive |
| **governance/data_adapter.py** | Multi-database adapter code |
| **test-data-automation/mongo_factories.py** | Data factory implementation |

---

## 🔐 Security Best Practices

1. **Never commit secrets**: Use `.env` files (already in `.gitignore`)
2. **Use strong passwords**: MongoDB Atlas enforces strong passwords
3. **Rotate credentials**: Periodically update database passwords
4. **Use network security**: Enable IP whitelist in MongoDB Atlas
5. **Enable authentication**: Always require username/password
6. **Audit access**: Monitor who accesses test data
7. **Mask sensitive data**: Use PII masking for email, phone, SSN

---

## 📞 Next Steps

1. **Set up `.env` file** with your MongoDB credentials
2. **Run health check** to verify connection
3. **Provision test data** for your collections
4. **Write your first test** using the factories
5. **Read ARCHITECTURE_DIAGRAMS.md** for visual overview

---

**Last Updated**: January 2026  
**Status**: Production Ready ✅  
**Security**: Safe for public Git repositories ✅
