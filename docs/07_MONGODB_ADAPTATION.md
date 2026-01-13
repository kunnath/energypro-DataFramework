# ISTA MongoDB Adaptation Guide

## 📋 Overview

This guide adapts the ISTA Test Data and Test Environment Automation Framework to work with **MongoDB** instead of PostgreSQL, while maintaining the ability to reuse the framework for other databases (MySQL, Postgres, DynamoDB, etc.).

### Your MongoDB Setup
- **Cloud Provider**: MongoDB Atlas
- **Cluster**: cluster0.zrzxfpd.mongodb.net
- **Database**: sample_mflix
- **Collections**: users, movies, comments, sessions
- **Connection String**: `mongodb+srv://aikunnath_db_user:demo123@cluster0.zrzxfpd.mongodb.net/sample_mflix`

---

## 🎯 Key Differences: MongoDB vs PostgreSQL

| Aspect | PostgreSQL | MongoDB |
|--------|------------|---------|
| **Schema** | Rigid (structured) | Flexible (document) |
| **Data Type** | Typed columns | JSON documents |
| **Constraints** | FK, PK, NOT NULL, CHECK | No native constraints |
| **Indexing** | B-tree indexes | BSON indexes |
| **Transactions** | ACID at table level | ACID at document level |
| **Scaling** | Vertical | Horizontal (sharding) |
| **Query Language** | SQL | MongoDB Query Language (MQL) |
| **Provisioning** | Schema + data | Documents |

### Framework Implications
1. **No schema introspection** → Use sample documents + Faker patterns
2. **No native constraints** → Validate in application layer
3. **No transactions** → Use document-level atomicity
4. **Flexible schema** → Allow field variations across documents
5. **No foreign keys** → Use ObjectId references + denormalization

---

## 🏗️ Architecture: Generic Database Adapter

The key to **database-agnostic framework** is an abstract `DataAdapter` interface:

```python
# governance/data_adapter.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class DataAdapter(ABC):
    """Abstract adapter for multiple database backends"""
    
    @abstractmethod
    def connect(self, connection_string: str) -> None:
        """Establish database connection"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Verify database connectivity"""
        pass
    
    @abstractmethod
    def create_collection(self, collection_name: str, schema: Dict) -> None:
        """Create table/collection with schema"""
        pass
    
    @abstractmethod
    def insert_documents(self, collection: str, documents: List[Dict]) -> int:
        """Insert documents; return count"""
        pass
    
    @abstractmethod
    def find_documents(self, collection: str, query: Dict) -> List[Dict]:
        """Query documents"""
        pass
    
    @abstractmethod
    def delete_documents(self, collection: str, query: Dict) -> int:
        """Delete documents; return count"""
        pass
    
    @abstractmethod
    def mask_field(self, collection: str, field: str, mask_fn) -> None:
        """Apply masking function to field"""
        pass
    
    @abstractmethod
    def get_collection_stats(self, collection: str) -> Dict:
        """Get document count, size, indexes"""
        pass


class MongoDBAdapter(DataAdapter):
    """MongoDB implementation of DataAdapter"""
    
    def __init__(self):
        from pymongo import MongoClient
        self.client: Optional[MongoClient] = None
        self.db = None
    
    def connect(self, connection_string: str) -> None:
        """Connect to MongoDB Atlas"""
        from pymongo import MongoClient
        self.client = MongoClient(connection_string)
        # Extract database name from connection string
        db_name = connection_string.split('/')[-1].split('?')[0]
        self.db = self.client[db_name]
    
    def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    def health_check(self) -> bool:
        """Verify MongoDB is accessible"""
        try:
            self.db.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB health check failed: {e}")
            return False
    
    def create_collection(self, collection_name: str, schema: Dict) -> None:
        """Create collection (MongoDB doesn't require pre-creation)"""
        if collection_name not in self.db.list_collection_names():
            self.db.create_collection(collection_name)
    
    def insert_documents(self, collection: str, documents: List[Dict]) -> int:
        """Insert documents into MongoDB collection"""
        if not documents:
            return 0
        
        result = self.db[collection].insert_many(documents)
        return len(result.inserted_ids)
    
    def find_documents(self, collection: str, query: Dict = None) -> List[Dict]:
        """Query MongoDB collection"""
        if query is None:
            query = {}
        return list(self.db[collection].find(query))
    
    def delete_documents(self, collection: str, query: Dict) -> int:
        """Delete documents from MongoDB collection"""
        result = self.db[collection].delete_many(query)
        return result.deleted_count
    
    def mask_field(self, collection: str, field: str, mask_fn) -> None:
        """Apply masking function to all documents"""
        docs = self.db[collection].find()
        bulk_ops = []
        
        for doc in docs:
            if field in doc and doc[field]:
                masked_value = mask_fn(doc[field])
                bulk_ops.append({
                    'update_one': {
                        'filter': {'_id': doc['_id']},
                        'update': {'$set': {field: masked_value}}
                    }
                })
        
        if bulk_ops:
            self.db[collection].bulk_write(
                [UpdateOne(op['filter'], op['update']) for op in bulk_ops]
            )
    
    def get_collection_stats(self, collection: str) -> Dict:
        """Get MongoDB collection statistics"""
        stats = self.db.command('collStats', collection)
        return {
            'count': stats['count'],
            'size': stats['size'],
            'avg_doc_size': stats.get('avgObjSize', 0),
            'indexes': len(stats.get('indexSizes', {}))
        }


class PostgreSQLAdapter(DataAdapter):
    """PostgreSQL implementation of DataAdapter"""
    # Similar implementation for PostgreSQL
    pass


class MySQLAdapter(DataAdapter):
    """MySQL implementation of DataAdapter"""
    # Similar implementation for MySQL
    pass
```

---

## 📊 MongoDB Collections Schema

### 1. **movies** Collection
```javascript
{
  "_id": ObjectId("..."),
  "title": "The Godfather",
  "year": 1972,
  "rated": "R",
  "runtime": 175,
  "genres": ["Crime", "Drama"],
  "director": "Francis Ford Coppola",
  "writers": ["Mario Puzo", "Francis Ford Coppola"],
  "cast": ["Marlon Brando", "Al Pacino"],
  "plot": "The aging patriarch of an organized crime empire...",
  "fullplot": "...",
  "languages": ["English"],
  "countries": ["USA"],
  "type": "movie",
  "tomatoes": {
    "viewer": { "rating": 9.2, "numReviews": 999 },
    "production": "...",
    "lastUpdated": ISODate("...")
  },
  "released": ISODate("1972-03-24"),
  "imdb": {
    "rating": 9.2,
    "votes": 1234567,
    "id": 68646
  },
  "awards": { "wins": 3, "nominations": 12 },
  "poster": "https://...",
  "metacritic": 100
}
```

### 2. **users** Collection
```javascript
{
  "_id": ObjectId("..."),
  "username": "john_doe",
  "email": "john@example.com",
  "password_hash": "hashed_password",
  "profile": {
    "name": "John Doe",
    "bio": "Movie enthusiast",
    "created_at": ISODate("2024-01-01")
  },
  "favorite_movies": [ObjectId("..."), ObjectId("...")],
  "watch_history": [
    {
      "movie_id": ObjectId("..."),
      "watched_at": ISODate("..."),
      "rating": 9
    }
  ],
  "preferences": {
    "genres": ["Drama", "Crime"],
    "language": "en",
    "notifications_enabled": true
  }
}
```

### 3. **comments** Collection
```javascript
{
  "_id": ObjectId("..."),
  "movie_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "text": "Amazing movie!",
  "date": ISODate("..."),
  "likes": 42,
  "is_hidden": false,
  "reviews": [
    {
      "reviewer_id": ObjectId("..."),
      "rating": 8,
      "text": "Great review"
    }
  ]
}
```

### 4. **sessions** Collection
```javascript
{
  "_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "token": "jwt_token",
  "created_at": ISODate("..."),
  "expires_at": ISODate("..."),
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

---

## 🔧 Test Data Definitions (YAML)

Create MongoDB-specific data specifications:

### `test-data-automation/data_definitions/mongodb/movies.yaml`
```yaml
apiVersion: data.automation/v1
kind: MongoDataDefinition
metadata:
  name: movies
  database: sample_mflix
  version: v1.0.0

spec:
  adapter: mongodb
  collection: movies
  volume:
    count: 100  # Generate 100 test movies
  
  fields:
    - name: title
      type: string
      generator: movie_title
    
    - name: year
      type: integer
      generator: year  # Random between 1900-2024
      min: 1900
      max: 2024
    
    - name: rated
      type: string
      generator: choice
      choices: ["G", "PG", "PG-13", "R", "NC-17"]
    
    - name: runtime
      type: integer
      generator: random_int
      min: 90
      max: 240
    
    - name: genres
      type: array
      generator: choice
      choices: ["Action", "Adventure", "Comedy", "Crime", "Drama", "Thriller"]
      cardinality: 2
    
    - name: director
      type: string
      generator: name
    
    - name: cast
      type: array
      generator: name
      cardinality: 5
    
    - name: plot
      type: string
      generator: text
      length: 200
    
    - name: released
      type: date
      generator: date_between
      start_date: "1900-01-01"
      end_date: "2024-01-01"
    
    - name: imdb
      type: object
      generator: object
      fields:
        - name: rating
          type: float
          generator: random_float
          min: 1.0
          max: 10.0
          precision: 1
        
        - name: votes
          type: integer
          generator: random_int
          min: 1000
          max: 1000000
```

### `test-data-automation/data_definitions/mongodb/users.yaml`
```yaml
apiVersion: data.automation/v1
kind: MongoDataDefinition
metadata:
  name: users
  database: sample_mflix
  version: v1.0.0

spec:
  adapter: mongodb
  collection: users
  volume:
    count: 50
  
  fields:
    - name: username
      type: string
      generator: username
      unique: true
    
    - name: email
      type: string
      generator: email
      masking: true
      masking_type: email
    
    - name: password_hash
      type: string
      generator: password_hash
      sensitive: true
    
    - name: profile
      type: object
      fields:
        - name: name
          type: string
          generator: name
        
        - name: bio
          type: string
          generator: text
          length: 100
        
        - name: created_at
          type: date
          generator: date_between
          start_date: "2024-01-01"
          end_date: "2024-12-31"
    
    - name: favorite_movies
      type: array
      generator: array
      cardinality: 5
      element_type: objectid
      reference_collection: movies
    
    - name: preferences
      type: object
      fields:
        - name: genres
          type: array
          generator: choice
          choices: ["Action", "Drama", "Thriller"]
          cardinality: 3
        
        - name: language
          type: string
          generator: choice
          choices: ["en", "es", "fr", "de"]
        
        - name: notifications_enabled
          type: boolean
          generator: choice
          choices: [true, false]
```

---

## 🐍 MongoDB Data Generation Classes

### `test-data-automation/mongo_schema_introspector.py`
```python
from typing import Dict, List, Any
from pymongo import MongoClient
from pymongo.errors import OperationFailure
import json

class MongoSchemaIntrospector:
    """Introspect MongoDB collection schema from sample documents"""
    
    def __init__(self, db):
        self.db = db
    
    def get_collection_schema(self, collection_name: str, sample_size: int = 10) -> Dict:
        """
        Analyze collection schema from sample documents
        
        Returns:
            {
                'collection': 'movies',
                'sample_count': 10,
                'fields': {
                    'title': {'type': 'string', 'nullable': False, 'examples': [...]},
                    'year': {'type': 'int', 'nullable': False, 'min': 1900, 'max': 2024},
                    'genres': {'type': 'array', 'element_type': 'string'},
                    'imdb': {'type': 'object', 'fields': {...}}
                }
            }
        """
        collection = self.db[collection_name]
        sample_docs = list(collection.find().limit(sample_size))
        
        if not sample_docs:
            return {'collection': collection_name, 'fields': {}}
        
        schema = {
            'collection': collection_name,
            'sample_count': len(sample_docs),
            'fields': {}
        }
        
        # Merge schemas from all samples
        all_field_names = set()
        for doc in sample_docs:
            all_field_names.update(doc.keys())
        
        for field_name in all_field_names:
            field_schema = self._infer_field_schema(field_name, sample_docs)
            schema['fields'][field_name] = field_schema
        
        return schema
    
    def _infer_field_schema(self, field_name: str, docs: List[Dict]) -> Dict:
        """Infer schema for a single field"""
        from bson import ObjectId
        
        field_schema = {
            'name': field_name,
            'types': set(),
            'nullable': False,
            'examples': [],
            'cardinality': set()
        }
        
        for doc in docs:
            if field_name not in doc:
                field_schema['nullable'] = True
                continue
            
            value = doc[field_name]
            python_type = type(value).__name__
            field_schema['types'].add(python_type)
            
            if python_type == 'list':
                field_schema['array'] = True
                if value:
                    field_schema['element_type'] = type(value[0]).__name__
                    field_schema['cardinality'].add(len(value))
                    if not field_schema['examples'] or len(field_schema['examples']) < 3:
                        field_schema['examples'].append(value)
            
            elif python_type == 'dict':
                field_schema['object'] = True
                field_schema['nested_fields'] = list(value.keys())
            
            elif isinstance(value, ObjectId):
                field_schema['type'] = 'objectid'
            
            elif isinstance(value, bool):
                field_schema['type'] = 'boolean'
            
            elif isinstance(value, str):
                field_schema['type'] = 'string'
                field_schema['length'] = len(value)
            
            elif isinstance(value, (int, float)):
                field_schema['type'] = 'number'
        
        # Clean up
        field_schema['types'] = list(field_schema['types'])
        field_schema['cardinality'] = list(field_schema['cardinality'])
        
        return field_schema


class MongoSchemaAwareGenerator:
    """Generate MongoDB documents respecting inferred schema"""
    
    def __init__(self, schema: Dict, data_definition: Dict):
        self.schema = schema
        self.data_definition = data_definition
    
    def generate_documents(self, count: int) -> List[Dict]:
        """Generate test documents"""
        from faker import Faker
        
        fake = Faker()
        documents = []
        
        for _ in range(count):
            doc = {}
            for field_name, field_def in self.data_definition.get('fields', {}).items():
                doc[field_name] = self._generate_field(field_def, fake)
            documents.append(doc)
        
        return documents
    
    def _generate_field(self, field_def: Dict, fake) -> Any:
        """Generate value for a field"""
        generator = field_def.get('generator')
        
        if generator == 'email':
            return fake.email()
        elif generator == 'name':
            return fake.name()
        elif generator == 'username':
            return fake.user_name()
        elif generator == 'movie_title':
            return fake.sentence(nb_words=3).rstrip('.')
        elif generator == 'year':
            return fake.random_int(min=field_def.get('min', 1900), 
                                   max=field_def.get('max', 2024))
        elif generator == 'choice':
            return fake.random.choice(field_def.get('choices', []))
        elif generator == 'array':
            return [self._generate_field({'generator': field_def.get('element_type')}, 
                                        fake) 
                   for _ in range(field_def.get('cardinality', 3))]
        elif generator == 'object':
            obj = {}
            for nested_field in field_def.get('fields', []):
                obj[nested_field['name']] = self._generate_field(nested_field, fake)
            return obj
        elif generator == 'objectid':
            from bson import ObjectId
            return ObjectId()
        elif generator == 'date_between':
            return fake.date_between(
                start_date=field_def.get('start_date'),
                end_date=field_def.get('end_date')
            )
        elif generator == 'password_hash':
            import hashlib
            return hashlib.sha256(fake.password().encode()).hexdigest()
        else:
            return fake.word()
```

---

## 🎯 MongoDB PII Masking

### `test-data-automation/mongo_pii_masker.py`
```python
import re
from typing import Any
from pymongo import MongoClient
from pymongo.operations import UpdateOne

class MongoPIIMasker:
    """Apply PII masking to MongoDB collections"""
    
    def __init__(self, db):
        self.db = db
    
    def mask_collection(self, collection_name: str, masking_config: Dict) -> int:
        """Apply masking rules to collection"""
        collection = self.db[collection_name]
        masked_count = 0
        
        for doc in collection.find():
            updates = {}
            
            for field_name, mask_type in masking_config.items():
                if field_name in doc and doc[field_name]:
                    masked_value = self._apply_mask(
                        doc[field_name], 
                        mask_type
                    )
                    updates[field_name] = masked_value
            
            if updates:
                collection.update_one(
                    {'_id': doc['_id']},
                    {'$set': updates}
                )
                masked_count += 1
        
        return masked_count
    
    @staticmethod
    def _apply_mask(value: Any, mask_type: str) -> str:
        """Apply specific masking function"""
        
        if mask_type == 'email':
            # john.doe@example.com → jo**@example.com
            match = re.match(r'(\w)(\w*)@(.+)', value)
            if match:
                return f"{match.group(1)}***@{match.group(3)}"
            return "masked@example.com"
        
        elif mask_type == 'phone':
            # +1-555-123-4567 → +1-555-***-****
            phone = str(value)
            if len(phone) >= 4:
                return phone[:-8] + '***-****'
            return '***-****'
        
        elif mask_type == 'ssn':
            # 123-45-6789 → ***-**-6789
            ssn = str(value)
            return '***-**-' + ssn[-4:]
        
        elif mask_type == 'credit_card':
            # 4532-1234-5678-9010 → ****-****-****-9010
            cc = str(value).replace('-', '')
            return '****-****-****-' + cc[-4:]
        
        elif mask_type == 'address':
            # Full address → [MASKED ADDRESS]
            return "[MASKED ADDRESS]"
        
        elif mask_type == 'password':
            # Any password → [HASHED]
            return "[HASHED]"
        
        elif mask_type == 'generic':
            # Generic field → [MASKED]
            return "[MASKED]"
        
        return value


# Usage Example
"""
db = MongoClient('mongodb+srv://user:pass@cluster.net/database').database
masker = MongoPIIMasker(db)

masking_config = {
    'email': 'email',
    'phone': 'phone',
    'ssn': 'ssn',
    'password_hash': 'password'
}

masked = masker.mask_collection('users', masking_config)
print(f"Masked {masked} documents")
"""
```

---

## 🐳 Docker Compose: MongoDB Setup

### `test-environment-automation/docker/docker-compose.mongodb.yml`
```yaml
version: '3.8'

services:
  # Local MongoDB for development (optional - can use Atlas)
  mongodb:
    image: mongo:7.0
    container_name: ista-mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: ista_user
      MONGO_INITDB_ROOT_PASSWORD: ista_password
      MONGO_INITDB_DATABASE: sample_mflix
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./mongodb/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test -u ista_user -p ista_password
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ista-network

  # Mongo Express (MongoDB Admin UI)
  mongo-express:
    image: mongo-express:latest
    container_name: ista-mongo-express
    ports:
      - "8081:8081"
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: ista_user
      ME_CONFIG_MONGODB_ADMINPASSWORD: ista_password
      ME_CONFIG_MONGODB_URL: mongodb://ista_user:ista_password@mongodb:27017/
      ME_CONFIG_MONGODB_ENABLE_ADMIN: 'true'
    depends_on:
      - mongodb
    networks:
      - ista-network

  # Data provisioning API
  ista-api:
    build:
      context: ../../test-data-automation
      dockerfile: Dockerfile.api
    container_name: ista-api
    environment:
      MONGODB_URI: mongodb://ista_user:ista_password@mongodb:27017/sample_mflix
      API_PORT: 8000
    ports:
      - "8000:8000"
    depends_on:
      mongodb:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ista-network

volumes:
  mongodb_data:

networks:
  ista-network:
    driver: bridge
```

---

## 📝 MongoDB CLI Tool

### `test-data-automation/ista_mongo_cli.py`
```python
import click
from rich.console import Console
from rich.table import Table
from pymongo import MongoClient
import yaml
import json
from datetime import datetime

console = Console()

@click.group()
def cli():
    """ISTA MongoDB Test Data Automation Tool"""
    pass

@cli.command()
@click.option('--mongodb-uri', required=True, help='MongoDB connection string')
@click.option('--databases', multiple=True, help='Databases to provision')
def provision(mongodb_uri: str, databases: tuple):
    """Provision test data into MongoDB"""
    with console.status("Connecting to MongoDB..."):
        client = MongoClient(mongodb_uri)
        db_name = mongodb_uri.split('/')[-1].split('?')[0]
        db = client[db_name]
    
    console.print(f"✓ Connected to {db_name}", style="green")
    
    # Load data definitions
    import os
    from pathlib import Path
    
    def_dir = Path('test-data-automation/data_definitions/mongodb')
    
    for collection_name in databases or os.listdir(def_dir):
        spec_file = def_dir / f"{collection_name}.yaml"
        
        if not spec_file.exists():
            console.print(f"✗ No definition for {collection_name}", style="red")
            continue
        
        with open(spec_file) as f:
            spec = yaml.safe_load(f)
        
        with console.status(f"Provisioning {collection_name}..."):
            # Generate and insert documents
            from mongo_schema_aware_generator import MongoSchemaAwareGenerator
            from faker import Faker
            
            generator = MongoSchemaAwareGenerator(spec, spec.get('spec', {}))
            volume = spec['spec']['volume']['count']
            
            docs = generator.generate_documents(volume)
            
            # Clear existing data
            db[collection_name].delete_many({})
            
            # Insert new data
            result = db[collection_name].insert_many(docs)
        
        console.print(f"✓ {collection_name}: {len(result.inserted_ids)} documents", 
                     style="green")
    
    client.close()

@cli.command()
@click.option('--mongodb-uri', required=True, help='MongoDB connection string')
def status(mongodb_uri: str):
    """Show status of MongoDB provisioning"""
    client = MongoClient(mongodb_uri)
    db_name = mongodb_uri.split('/')[-1].split('?')[0]
    db = client[db_name]
    
    table = Table(title=f"MongoDB: {db_name}")
    table.add_column("Collection", style="cyan")
    table.add_column("Documents", style="magenta")
    table.add_column("Size (MB)", style="green")
    
    for collection_name in db.list_collection_names():
        stats = db.command('collStats', collection_name)
        doc_count = stats['count']
        size_mb = stats['size'] / (1024 * 1024)
        
        table.add_row(collection_name, str(doc_count), f"{size_mb:.2f}")
    
    console.print(table)
    client.close()

@cli.command()
@click.option('--mongodb-uri', required=True, help='MongoDB connection string')
@click.option('--collections', multiple=True, help='Collections to cleanup')
def cleanup(mongodb_uri: str, collections: tuple):
    """Clean up test data from MongoDB"""
    client = MongoClient(mongodb_uri)
    db_name = mongodb_uri.split('/')[-1].split('?')[0]
    db = client[db_name]
    
    target_collections = collections or db.list_collection_names()
    
    for collection_name in target_collections:
        result = db[collection_name].delete_many({})
        console.print(f"✓ Deleted {result.deleted_count} documents from {collection_name}", 
                     style="green")
    
    client.close()

if __name__ == '__main__':
    cli()
```

---

## ✅ Next Steps

1. **Update requirements.txt** with MongoDB dependencies:
```
pymongo>=4.5.0
pymongo-cloud>=0.1.0
motor>=3.3.0  # Async MongoDB driver
faker>=20.0.0
```

2. **Test with sample_mflix**:
```bash
# Start local MongoDB
docker-compose -f test-environment-automation/docker/docker-compose.mongodb.yml up -d

# OR use your Atlas cluster directly
export MONGODB_URI="mongodb+srv://aikunnath_db_user:demo123@cluster0.zrzxfpd.mongodb.net/sample_mflix"

# Provision data
python test-data-automation/ista_mongo_cli.py provision \
  --mongodb-uri "$MONGODB_URI" \
  --databases movies users comments

# Check status
python test-data-automation/ista_mongo_cli.py status \
  --mongodb-uri "$MONGODB_URI"
```

3. **Implement data factories** for movies, users, comments

4. **Adapt governance** for MongoDB (masking, audit logging)

5. **Create example tests** using MongoDB test data

---

## 🔄 Database Reusability

Once you implement `DataAdapter` abstraction, you can reuse framework for:

| Database | Adapter | Connection |
|----------|---------|-----------|
| MongoDB | ✅ Built | `mongodb+srv://...` |
| PostgreSQL | Create `PostgreSQLAdapter` | `postgresql://user:pass@host/db` |
| MySQL | Create `MySQLAdapter` | `mysql://user:pass@host/db` |
| DynamoDB | Create `DynamoDBAdapter` | AWS SDK |
| Firestore | Create `FirestoreAdapter` | Google Cloud SDK |

---

## 📊 Architecture Comparison

```
┌─────────────────────┐
│  Test Framework     │
│  (Database Agnostic)│
└──────────┬──────────┘
           │
    ┌──────┴──────────────────┬─────────────────┐
    │                         │                 │
    ▼                         ▼                 ▼
┌────────────┐         ┌────────────┐    ┌─────────────┐
│ Mongo      │         │ Postgres   │    │ MySQL       │
│ Adapter    │         │ Adapter    │    │ Adapter     │
└──────┬─────┘         └──────┬─────┘    └──────┬──────┘
       │                      │                 │
       ▼                      ▼                 ▼
   MongoDB             PostgreSQL            MySQL
   Atlas               RDS                   RDS
```

---

**Status**: Ready for MongoDB Implementation  
**Estimated Time**: 2 weeks for full MongoDB support  
**Reusability**: Framework designed for multi-database support
