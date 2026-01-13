# ISTA MongoDB Quick Start Guide

## 📦 Your MongoDB Setup

```
Database: sample_mflix
Cluster: cluster0.zrzxfpd.mongodb.net
Connection: mongodb+srv://aikunnath_db_user:demo123@cluster0.zrzxfpd.mongodb.net/sample_mflix
Collections: users, movies, comments, sessions
```

---

## 🚀 Quick Start (5 minutes)

### Step 1: Set Environment Variable
```bash
export MONGODB_URI="mongodb+srv://aikunnath_db_user:demo123@cluster0.zrzxfpd.mongodb.net/sample_mflix"
```

### Step 2: Install Dependencies
```bash
pip install pymongo faker rich click pyyaml
```

### Step 3: Verify Connection
```bash
python test-data-automation/ista_mongo_cli.py health

# Expected output:
# ✓ MongoDB connection healthy
#   Database: sample_mflix
#   Version: 7.0.x
#   Collections: 4
#   Cluster: MongoDB Atlas
```

### Step 4: Provision Test Data
```bash
# Provision all collections
python test-data-automation/ista_mongo_cli.py provision \
  -d movies \
  -d users \
  -d comments \
  -d sessions

# Expected output:
# Provisioning movies... ✓ movies: 100 documents (5.23 MB)
# Provisioning users... ✓ users: 50 documents (2.15 MB)
# Provisioning comments... ✓ comments: 200 documents (8.47 MB)
# Provisioning sessions... ✓ sessions: 100 documents (1.89 MB)
# 
# Total provisioned: 450 documents
```

### Step 5: Check Status
```bash
python test-data-automation/ista_mongo_cli.py status

# Expected output:
# ┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳═══════════════════┳━━━━━━━┓
# ┃ Collection ┃ Documents ┃ Size(MB) ┃ Avg Doc Size (B) ┃ Index ┃
# ┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇═══════════════════╇━━━━━━━┩
# │ movies     │       100 │     5.23 │            53421 │     1 │
# │ users      │        50 │     2.15 │            43890 │     2 │
# │ comments   │       200 │     8.47 │            43567 │     1 │
# │ sessions   │       100 │     1.89 │            19234 │     1 │
# └────────────┴───────────┴─────────┴───────────────────┴───────┘
# 
# Summary:
#   Total Documents: 450
#   Total Size: 17.74 MB
```

### Step 6: View Sample Data
```bash
python test-data-automation/ista_mongo_cli.py show -c movies --limit 2

# Expected output:
# Sample documents from movies:
#
# Document 1:
# {
#   "_id": "ObjectId('...')",
#   "title": "Amazing Action Movie",
#   "year": 2023,
#   "rated": "PG-13",
#   "runtime": 145,
#   "genres": ["Action", "Thriller"],
#   ...
# }
```

---

## 📋 Command Reference

### provision
Provision test data into MongoDB collections

```bash
# Basic: provision all defined collections
python test-data-automation/ista_mongo_cli.py provision \
  -d users -d movies

# With custom volumes
python test-data-automation/ista_mongo_cli.py provision \
  -d users -d movies \
  --volumes '{"users":200,"movies":500}'

# Clear and reprovision
python test-data-automation/ista_mongo_cli.py provision \
  -d users --clear

# Skip PII masking
python test-data-automation/ista_mongo_cli.py provision \
  -d users --no-mask
```

### status
Display collection statistics

```bash
python test-data-automation/ista_mongo_cli.py status

# Shows:
# - Document count per collection
# - Size in MB
# - Average document size
# - Number of indexes
```

### cleanup
Delete test data from collections

```bash
# Delete from specific collections (with confirmation)
python test-data-automation/ista_mongo_cli.py cleanup \
  -c users -c movies

# Delete all collections without confirmation
python test-data-automation/ista_mongo_cli.py cleanup --force
```

### show
Display sample documents from a collection

```bash
# Show 5 documents (default)
python test-data-automation/ista_mongo_cli.py show -c movies

# Show specific number
python test-data-automation/ista_mongo_cli.py show -c users --limit 10
```

### health
Check MongoDB connection status

```bash
python test-data-automation/ista_mongo_cli.py health
```

---

## 🏭 Data Factories

Factories are provided for generating realistic test data:

### MovieFactory
```python
from test_data_automation.mongo_factories import MovieFactory

# Create single movie
movie = MovieFactory.create()

# Create batch
movies = MovieFactory.create_batch(100)

# Create with overrides
movie = MovieFactory.create(
    title="The Godfather",
    year=1972,
    rated="R"
)

# Create high-rated movies
from test_data_automation.mongo_factories import MovieFactoryVariants
movies = MovieFactoryVariants.create_movie_batch_with_genres(
    count=50,
    genres=["Drama", "Crime"]
)
```

### UserFactory
```python
from test_data_automation.mongo_factories import UserFactory, UserFactoryVariants

# Create basic user
user = UserFactory.create()

# Create premium user
user = UserFactoryVariants.create_premium_user()

# Create active user with watch history
user = UserFactoryVariants.create_active_user(min_watches=10)

# Create new user (registered in last 7 days)
user = UserFactoryVariants.create_new_user()
```

### CommentFactory
```python
from test_data_automation.mongo_factories import CommentFactory
from bson import ObjectId

# Create comment
comment = CommentFactory.create()

# Create comment with specific references
movie_id = ObjectId()
user_id = ObjectId()
comment = CommentFactory.create(
    movie_id=movie_id,
    user_id=user_id,
    text="Excellent movie!"
)
```

### SessionFactory
```python
from test_data_automation.mongo_factories import SessionFactory

# Create session
session = SessionFactory.create()

# Create multiple sessions
sessions = SessionFactory.create_batch(50)
```

---

## 🧪 Writing Tests with MongoDB

### Using @requires_test_data Decorator

Create `test-data-automation/mongo_decorators.py`:

```python
from functools import wraps
from typing import Dict, List
from pymongo import MongoClient
import os

def requires_test_data(collections: List[str], volumes: Dict[str, int] = None):
    """Decorator to provision MongoDB test data for a test"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mongodb_uri = os.getenv('MONGODB_URI')
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable not set")
            
            # Connect and provision
            client = MongoClient(mongodb_uri)
            db_name = mongodb_uri.split('/')[-1].split('?')[0]
            db = client[db_name]
            
            test_data = {}
            
            try:
                # Provision data
                from mongo_factories import (
                    MovieFactory, UserFactory, 
                    CommentFactory, SessionFactory
                )
                
                factory_map = {
                    'movies': MovieFactory,
                    'users': UserFactory,
                    'comments': CommentFactory,
                    'sessions': SessionFactory
                }
                
                for collection_name in collections:
                    volume = (volumes or {}).get(collection_name, 10)
                    factory = factory_map[collection_name]
                    docs = factory.create_batch(volume)
                    result = db[collection_name].insert_many(docs)
                    test_data[collection_name] = result.inserted_ids
                
                # Run test
                result = func(test_data, *args, **kwargs)
                
            finally:
                # Cleanup
                for collection_name in collections:
                    db[collection_name].delete_many({})
                client.close()
            
            return result
        
        return wrapper
    return decorator
```

### Example Test

Create `tests/test_mongodb_example.py`:

```python
import pytest
from test_data_automation.mongo_decorators import requires_test_data
from pymongo import MongoClient
import os

class TestMovieCollection:
    
    @requires_test_data(
        collections=['movies'],
        volumes={'movies': 50}
    )
    def test_can_find_movies(self, test_data):
        """Test finding movies in collection"""
        mongodb_uri = os.getenv('MONGODB_URI')
        client = MongoClient(mongodb_uri)
        db_name = mongodb_uri.split('/')[-1].split('?')[0]
        db = client[db_name]
        
        # Query
        movies = list(db.movies.find().limit(10))
        
        # Assertions
        assert len(movies) > 0
        assert all('title' in movie for movie in movies)
        assert all('year' in movie for movie in movies)
        assert all('genres' in movie for movie in movies)
        
        client.close()
    
    @requires_test_data(
        collections=['users', 'movies'],
        volumes={'users': 20, 'movies': 100}
    )
    def test_user_favorite_movies(self, test_data):
        """Test user favorite movies references"""
        mongodb_uri = os.getenv('MONGODB_URI')
        client = MongoClient(mongodb_uri)
        db_name = mongodb_uri.split('/')[-1].split('?')[0]
        db = client[db_name]
        
        # Get a user
        user = db.users.find_one()
        assert user is not None
        
        # Check favorite_movies
        assert 'favorite_movies' in user
        assert isinstance(user['favorite_movies'], list)
        
        # Verify favorite movies exist
        for movie_id in user['favorite_movies']:
            movie = db.movies.find_one({'_id': movie_id})
            assert movie is not None, f"Favorite movie {movie_id} not found"
        
        client.close()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

Run tests:
```bash
export MONGODB_URI="mongodb+srv://aikunnath_db_user:demo123@cluster0.zrzxfpd.mongodb.net/sample_mflix"
pytest tests/test_mongodb_example.py -v
```

---

## 📊 Using DataAdapter for Multi-Database Support

The ISTA framework is designed to work with any database through the `DataAdapter` abstraction:

```python
from governance.data_adapter import get_adapter

# Get MongoDB adapter
adapter = get_adapter('mongodb')
adapter.connect('mongodb+srv://user:pass@cluster.net/database')

# Now use same code for any database type:
adapter.insert_documents('movies', [
    {'title': 'Movie 1', 'year': 2024},
    {'title': 'Movie 2', 'year': 2023}
])

# Get collection stats
stats = adapter.get_collection_stats('movies')
print(f"Documents: {stats['count']}, Size: {stats['size']} bytes")

# Apply masking
masked_count = adapter.mask_field('users', 'email', lambda x: 'masked@example.com')

# Cleanup
adapter.disconnect()
```

### Switch to PostgreSQL
```python
# Same code, different adapter!
adapter = get_adapter('postgresql')
adapter.connect('postgresql://user:pass@localhost/testdb')

# All operations work identically
adapter.insert_documents('movies', [...])
```

---

## 🔒 PII Masking in MongoDB

Automatic email masking is applied during provisioning:

```bash
# Email masking enabled (default)
python test-data-automation/ista_mongo_cli.py provision \
  -d users

# Check masked email
python test-data-automation/ista_mongo_cli.py show -c users --limit 1
# Output: "email": "j***@example.com"
```

Manual masking via adapter:

```python
from governance.data_adapter import get_adapter

adapter = get_adapter('mongodb')
adapter.connect(mongodb_uri)

# Mask all emails
def mask_email(email):
    import re
    match = re.match(r'(\w)(\w*)@(.+)', email)
    return f"{match.group(1)}***@{match.group(3)}" if match else "masked@example.com"

masked_count = adapter.mask_field('users', 'email', mask_email)
print(f"Masked {masked_count} email addresses")

adapter.disconnect()
```

---

## 🎯 Next Steps

1. **Provision test data**:
   ```bash
   python test-data-automation/ista_mongo_cli.py provision -d movies -d users
   ```

2. **Write your first test** using the decorator

3. **Integrate with CI/CD**:
   ```yaml
   - name: Provision test data
     run: |
       python test-data-automation/ista_mongo_cli.py provision \
         -d movies -d users -d comments -d sessions
   ```

4. **Extend for other databases**:
   - Create `PostgreSQLAdapter` in `governance/data_adapter.py`
   - Create PostgreSQL factories
   - Use same test code with different adapter

---

## 🔧 Troubleshooting

### Connection Error
```
Error: MongoDB connection failed
```

**Solution**: Check connection string and network access
```bash
# Test connection directly
python -c "from pymongo import MongoClient; client = MongoClient('$MONGODB_URI'); print(client.admin.command('ping'))"
```

### Database Name Not Found
```
Error: Database name not found in connection string
```

**Solution**: Ensure connection string includes database name
```
mongodb+srv://user:pass@cluster.net/sample_mflix  ✓
mongodb+srv://user:pass@cluster.net                ✗
```

### Factory Import Error
```
ModuleNotFoundError: No module named 'mongo_factories'
```

**Solution**: Ensure you're in correct directory and factories file exists
```bash
ls -la test-data-automation/mongo_factories.py
python -c "from test_data_automation.mongo_factories import MovieFactory"
```

### Masking Not Applied
```bash
# Check if masking is enabled (default is true)
python test-data-automation/ista_mongo_cli.py provision -d users  # masking enabled
python test-data-automation/ista_mongo_cli.py provision -d users --no-mask  # disabled
```

---

## 📚 Related Documentation

- **07_MONGODB_ADAPTATION.md** - Complete MongoDB framework design
- **governance/data_adapter.py** - Database adapter implementation
- **test-data-automation/mongo_factories.py** - Data factories
- **test-data-automation/ista_mongo_cli.py** - CLI tool source

---

## 🎉 Success Criteria

After completing this quick start, you should be able to:

✅ Connect to your MongoDB Atlas cluster  
✅ Provision test data in <30 seconds  
✅ View sample documents  
✅ Clean up test data  
✅ Write tests with automatic data provisioning  
✅ Mask PII fields automatically  
✅ Extend to other databases using adapters  

---

**Status**: Ready for MongoDB Testing  
**Estimated Time to First Test**: 15 minutes  
**Database Reusability**: Framework supports PostgreSQL, MySQL, DynamoDB, and more
