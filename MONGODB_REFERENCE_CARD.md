# ISTA MongoDB Reference Card

## 📋 Quick Commands

### Setup
```bash
# Install dependencies
pip install pymongo faker rich click pyyaml

# Set environment variable
export MONGODB_URI="mongodb+srv://aikunnath_db_user:demo123@cluster0.zrzxfpd.mongodb.net/sample_mflix"
```

### Provisioning
```bash
# Provision all collections
python test-data-automation/ista_mongo_cli.py provision -d movies -d users -d comments -d sessions

# Provision with custom volumes
python test-data-automation/ista_mongo_cli.py provision -d movies --volumes '{"movies":200}'

# Clear and reprovision
python test-data-automation/ista_mongo_cli.py provision -d users --clear

# Skip PII masking
python test-data-automation/ista_mongo_cli.py provision -d users --no-mask
```

### Verification
```bash
# Check connection
python test-data-automation/ista_mongo_cli.py health

# Show status/statistics
python test-data-automation/ista_mongo_cli.py status

# View sample documents
python test-data-automation/ista_mongo_cli.py show -c movies --limit 3
```

### Cleanup
```bash
# Delete data from specific collections
python test-data-automation/ista_mongo_cli.py cleanup -c users -c movies

# Delete all collections
python test-data-automation/ista_mongo_cli.py cleanup --force
```

---

## 🏭 Data Factories

### MovieFactory
```python
from test_data_automation.mongo_factories import MovieFactory, MovieFactoryVariants

# Single movie
movie = MovieFactory.create()

# Batch
movies = MovieFactory.create_batch(100)

# With overrides
movie = MovieFactory.create(title="The Godfather", year=1972)

# Variants
classic = MovieFactoryVariants.create_classic_movie()
modern = MovieFactoryVariants.create_modern_movie()
high_rated = MovieFactoryVariants.create_high_rated_movie()
```

### UserFactory
```python
from test_data_automation.mongo_factories import UserFactory, UserFactoryVariants

# Single user
user = UserFactory.create()

# Batch
users = UserFactory.create_batch(50)

# Variants
premium = UserFactoryVariants.create_premium_user()
new = UserFactoryVariants.create_new_user()
active = UserFactoryVariants.create_active_user(min_watches=5)
```

### CommentFactory
```python
from test_data_automation.mongo_factories import CommentFactory
from bson import ObjectId

# Single comment
comment = CommentFactory.create()

# With references
movie_id = ObjectId()
user_id = ObjectId()
comment = CommentFactory.create(movie_id=movie_id, user_id=user_id)
```

### SessionFactory
```python
from test_data_automation.mongo_factories import SessionFactory

# Single session
session = SessionFactory.create()

# Batch
sessions = SessionFactory.create_batch(100)
```

---

## 🔌 Using DataAdapter

### Connect to Database
```python
from governance.data_adapter import get_adapter

# Get adapter
adapter = get_adapter('mongodb')

# Connect
adapter.connect('mongodb+srv://user:pass@cluster.net/database')

# Check health
if adapter.health_check():
    print("Connected!")
```

### Perform Operations
```python
# Insert documents
count = adapter.insert_documents('movies', [
    {'title': 'Movie 1', 'year': 2024},
    {'title': 'Movie 2', 'year': 2023}
])

# Query documents
movies = adapter.find_documents('movies', {'year': {'$gte': 2020}})

# Count documents
total = adapter.count_documents('movies')

# Update documents
updated = adapter.update_documents('movies', 
    {'year': 2020}, 
    {'year': 2021}
)

# Delete documents
deleted = adapter.delete_documents('movies', {'year': {'$lt': 1950}})

# Get statistics
stats = adapter.get_collection_stats('movies')
# {'count': 100, 'size': 5234567, 'avg_doc_size': 52345, 'indexes': 2}
```

### Apply Masking
```python
# Mask a field
def mask_email(email):
    import re
    match = re.match(r'(\w)(\w*)@(.+)', email)
    return f"{match.group(1)}***@{match.group(3)}" if match else "masked@example.com"

masked = adapter.mask_field('users', 'email', mask_email)
print(f"Masked {masked} documents")
```

### Get Schema
```python
schema = adapter.get_schema('users', sample_size=10)
print(f"Collection: {schema.name}")
for field_name, field_schema in schema.fields.items():
    print(f"  {field_name}: {field_schema.type}")
```

### Disconnect
```python
adapter.disconnect()
```

---

## 📝 Writing Tests

### Basic Test
```python
import pytest
from pymongo import MongoClient
import os

def test_movie_collection():
    """Test movie collection"""
    mongodb_uri = os.getenv('MONGODB_URI')
    client = MongoClient(mongodb_uri)
    db = client['sample_mflix']
    
    # Query
    movies = list(db.movies.find().limit(5))
    
    # Assert
    assert len(movies) > 0
    assert all('title' in m for m in movies)
    
    client.close()
```

### With Data Provisioning
```python
from test_data_automation.mongo_factories import MovieFactory, UserFactory
from pymongo import MongoClient
import os

@pytest.fixture
def setup_test_data():
    """Provision and cleanup test data"""
    mongodb_uri = os.getenv('MONGODB_URI')
    client = MongoClient(mongodb_uri)
    db = client['sample_mflix']
    
    # Provision
    movies = MovieFactory.create_batch(10)
    users = UserFactory.create_batch(5)
    db.movies.insert_many(movies)
    db.users.insert_many(users)
    
    yield db
    
    # Cleanup
    db.movies.delete_many({})
    db.users.delete_many({})
    client.close()

def test_with_fixtures(setup_test_data):
    """Test using fixtures"""
    db = setup_test_data
    
    movies = list(db.movies.find())
    assert len(movies) == 10
    
    users = list(db.users.find())
    assert len(users) == 5
```

---

## 🗂️ Directory Structure

```
/Users/kunnath/Projects/Ista/
├── QUICK_START.md                    # General framework guide
├── MONGODB_QUICK_START.md            # MongoDB-specific guide
├── MONGODB_IMPLEMENTATION_SUMMARY.md  # This implementation
├── requirements.txt                  # Python dependencies
│
├── docs/
│   ├── 01-06_*.md                   # Original framework docs
│   └── 07_MONGODB_ADAPTATION.md      # MongoDB design
│
├── governance/
│   └── data_adapter.py              # Database adapter abstraction
│
└── test-data-automation/
    ├── ista_mongo_cli.py            # MongoDB CLI tool
    ├── mongo_factories.py           # Data factories
    ├── ista_data_cli.py             # Original PostgreSQL CLI
    └── data_definitions/
        └── mongodb/
            ├── movies.yaml          # Movie spec
            ├── users.yaml           # User spec
            ├── comments.yaml        # Comment spec (TODO)
            └── sessions.yaml        # Session spec (TODO)
```

---

## 🔍 Common Queries

### Count Documents by Field
```python
from pymongo import MongoClient

client = MongoClient('mongodb+srv://...')
db = client['sample_mflix']

# Count by year
pipeline = [
    {'$group': {'_id': '$year', 'count': {'$sum': 1}}}
]
results = list(db.movies.aggregate(pipeline))
```

### Find Documents with Specific Conditions
```python
# Find rated R movies from 2020+
movies = db.movies.find({
    'rated': 'R',
    'year': {'$gte': 2020}
})

# Find users with premium subscription
users = db.users.find({
    'subscription.plan': 'premium',
    'subscription.active': True
})

# Find movies with high IMDB rating
high_rated = db.movies.find({
    'imdb.rating': {'$gte': 8.0}
})
```

### Update Multiple Documents
```python
# Activate all expired subscriptions
db.users.update_many(
    {'subscription.active': False},
    {'$set': {'subscription.active': True}}
)

# Add field to all documents
db.movies.update_many(
    {},
    {'$set': {'test_data': True}}
)
```

### Delete Documents Matching Criteria
```python
# Delete old sessions (older than 30 days)
from datetime import datetime, timedelta

thirty_days_ago = datetime.now() - timedelta(days=30)
deleted = db.sessions.delete_many({
    'created_at': {'$lt': thirty_days_ago}
})
print(f"Deleted {deleted.deleted_count} sessions")
```

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Check MONGODB_URI, network access, IP whitelist |
| No collections found | Database name may be incorrect, verify URI |
| Import error | Run `pip install pymongo faker rich click pyyaml` |
| Permission denied | Check user credentials, ensure user has access to database |
| Slow provisioning | Reduce volume, check network, increase batch size |
| Masking not applied | Ensure `--no-mask` flag not used, check field names |
| Tests flaky | Ensure cleanup runs, check data isolation, add retries |

---

## 📚 Documentation

| Document | Audience |
|----------|----------|
| QUICK_START.md | All users |
| MONGODB_QUICK_START.md | MongoDB users |
| MONGODB_IMPLEMENTATION_SUMMARY.md | Architects |
| 07_MONGODB_ADAPTATION.md | Technical leads |
| governance/data_adapter.py | Backend engineers |
| test-data-automation/mongo_factories.py | Test engineers |

---

## ✅ Checklist for MongoDB Setup

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Set MONGODB_URI environment variable
- [ ] Run health check: `ista health`
- [ ] Provision test data: `ista provision -d movies -d users`
- [ ] Check status: `ista status`
- [ ] View sample data: `ista show -c movies`
- [ ] Write first test
- [ ] Run test with data
- [ ] Cleanup data: `ista cleanup --force`
- [ ] Integrate with CI/CD

---

## 🎯 Key Concepts

| Concept | Meaning |
|---------|---------|
| **DataAdapter** | Abstract interface for any database |
| **Factory** | Class that generates realistic test data |
| **Collection** | MongoDB equivalent of SQL table |
| **Document** | MongoDB record/row |
| **ObjectId** | MongoDB primary key |
| **YAML Spec** | Data definition file |
| **PII** | Personally Identifiable Information (masked) |
| **Provisioning** | Creating test data |
| **Cleanup** | Deleting test data |

---

## 🔗 Environment Variables

```bash
# Required
MONGODB_URI="mongodb+srv://user:pass@cluster.net/database"

# Optional
ISTA_LOG_LEVEL=INFO          # Logging level
ISTA_BATCH_SIZE=100          # Documents per batch
ISTA_TIMEOUT=30              # Connection timeout (seconds)
ISTA_MASK_ENABLED=true       # PII masking
ISTA_VERIFY_SSL=true         # Verify SSL certificates
```

---

## 📊 Performance Tips

1. **Batch Operations**: Insert documents in batches of 100-1000
2. **Connection Pooling**: Reuse connections; don't create new ones per operation
3. **Indexing**: Create indexes on frequently queried fields
4. **Parallel Tests**: Use pytest-xdist for parallel execution
5. **Data Cleanup**: Always cleanup after tests to avoid disk bloat

---

**Version**: 1.0  
**Last Updated**: January 2026  
**Status**: Production Ready  
**Support**: See MONGODB_QUICK_START.md for detailed help
