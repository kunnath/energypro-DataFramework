"""
DataAdapter: Database-agnostic interface for ISTA framework

This module provides an abstract interface that allows the ISTA framework
to work with MongoDB, PostgreSQL, MySQL, DynamoDB, and other databases
without code changes.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentSchema:
    """Schema information for a document/row"""
    name: str
    fields: Dict[str, 'FieldSchema']
    primary_key: str = '_id'


@dataclass
class FieldSchema:
    """Schema information for a single field"""
    name: str
    type: str  # 'string', 'integer', 'float', 'boolean', 'date', 'object', 'array'
    nullable: bool = True
    indexed: bool = False
    unique: bool = False
    reference: Optional[str] = None  # For foreign keys / references


class DataAdapter(ABC):
    """
    Abstract adapter for multiple database backends.
    
    All database implementations (MongoDB, PostgreSQL, MySQL, etc.) should
    inherit from this class and implement all abstract methods.
    """
    
    @abstractmethod
    def connect(self, connection_string: str, **options) -> None:
        """
        Establish connection to database
        
        Args:
            connection_string: Database-specific connection URL
            **options: Additional connection options
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Verify database connectivity and basic operations.
        
        Returns:
            True if database is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def create_collection(self, collection_name: str, schema: Optional[Dict] = None) -> None:
        """
        Create a collection/table with optional schema.
        
        Args:
            collection_name: Name of collection/table to create
            schema: Optional schema definition
        """
        pass
    
    @abstractmethod
    def drop_collection(self, collection_name: str) -> None:
        """
        Drop a collection/table.
        
        Args:
            collection_name: Name of collection/table to drop
        """
        pass
    
    @abstractmethod
    def list_collections(self) -> List[str]:
        """
        List all collections/tables in database.
        
        Returns:
            List of collection names
        """
        pass
    
    @abstractmethod
    def insert_documents(self, collection: str, documents: List[Dict]) -> int:
        """
        Insert multiple documents.
        
        Args:
            collection: Collection/table name
            documents: List of document dictionaries
        
        Returns:
            Number of documents inserted
        """
        pass
    
    @abstractmethod
    def insert_one(self, collection: str, document: Dict) -> Any:
        """
        Insert a single document.
        
        Args:
            collection: Collection/table name
            document: Document dictionary
        
        Returns:
            ID of inserted document
        """
        pass
    
    @abstractmethod
    def find_documents(self, collection: str, query: Optional[Dict] = None, 
                      limit: int = 0, skip: int = 0) -> List[Dict]:
        """
        Query documents.
        
        Args:
            collection: Collection/table name
            query: Query filter (None = all documents)
            limit: Maximum documents to return (0 = unlimited)
            skip: Number of documents to skip
        
        Returns:
            List of matching documents
        """
        pass
    
    @abstractmethod
    def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        """
        Find a single document.
        
        Args:
            collection: Collection/table name
            query: Query filter
        
        Returns:
            First matching document or None
        """
        pass
    
    @abstractmethod
    def count_documents(self, collection: str, query: Optional[Dict] = None) -> int:
        """
        Count documents matching query.
        
        Args:
            collection: Collection/table name
            query: Query filter (None = all documents)
        
        Returns:
            Count of matching documents
        """
        pass
    
    @abstractmethod
    def update_documents(self, collection: str, query: Dict, update: Dict) -> int:
        """
        Update multiple documents.
        
        Args:
            collection: Collection/table name
            query: Query filter
            update: Update operations
        
        Returns:
            Number of documents updated
        """
        pass
    
    @abstractmethod
    def update_one(self, collection: str, query: Dict, update: Dict) -> bool:
        """
        Update a single document.
        
        Args:
            collection: Collection/table name
            query: Query filter
            update: Update operations
        
        Returns:
            True if document was updated
        """
        pass
    
    @abstractmethod
    def delete_documents(self, collection: str, query: Dict) -> int:
        """
        Delete multiple documents.
        
        Args:
            collection: Collection/table name
            query: Query filter
        
        Returns:
            Number of documents deleted
        """
        pass
    
    @abstractmethod
    def delete_one(self, collection: str, query: Dict) -> bool:
        """
        Delete a single document.
        
        Args:
            collection: Collection/table name
            query: Query filter
        
        Returns:
            True if document was deleted
        """
        pass
    
    @abstractmethod
    def bulk_write(self, collection: str, operations: List[Dict]) -> Dict:
        """
        Execute bulk write operations.
        
        Args:
            collection: Collection/table name
            operations: List of write operations
        
        Returns:
            Summary of operations performed
        """
        pass
    
    @abstractmethod
    def create_index(self, collection: str, field_name: str, unique: bool = False) -> None:
        """
        Create an index on a field.
        
        Args:
            collection: Collection/table name
            field_name: Field to index
            unique: Whether index should enforce uniqueness
        """
        pass
    
    @abstractmethod
    def get_collection_stats(self, collection: str) -> Dict:
        """
        Get collection statistics.
        
        Returns:
            Dictionary with 'count', 'size', 'avg_doc_size', 'indexes'
        """
        pass
    
    @abstractmethod
    def mask_field(self, collection: str, field: str, mask_fn) -> int:
        """
        Apply masking function to field across all documents.
        
        Args:
            collection: Collection/table name
            field: Field to mask
            mask_fn: Function that masks a value
        
        Returns:
            Number of documents masked
        """
        pass
    
    @abstractmethod
    def get_schema(self, collection: str, sample_size: int = 10) -> DocumentSchema:
        """
        Infer schema from collection.
        
        Args:
            collection: Collection/table name
            sample_size: Number of documents to sample
        
        Returns:
            DocumentSchema with field information
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> Tuple[bool, str]:
        """
        Validate database connection with detailed message.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        pass


class MongoDBAdapter(DataAdapter):
    """MongoDB implementation of DataAdapter using pymongo"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connection_string = None
    
    def connect(self, connection_string: str, **options) -> None:
        """Connect to MongoDB"""
        from pymongo import MongoClient
        
        try:
            self.client = MongoClient(connection_string, **options)
            # Extract database name from connection string
            db_name = connection_string.split('/')[-1].split('?')[0]
            if not db_name:
                raise ValueError("Database name not found in connection string")
            self.db = self.client[db_name]
            self.connection_string = connection_string
            logger.info(f"Connected to MongoDB database: {db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def health_check(self) -> bool:
        """Verify MongoDB connectivity"""
        try:
            self.db.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False
    
    def validate_connection(self) -> Tuple[bool, str]:
        """Validate MongoDB connection"""
        try:
            self.db.client.admin.command('ping')
            return True, f"Connected to MongoDB: {self.db.name}"
        except Exception as e:
            return False, f"MongoDB connection failed: {str(e)}"
    
    def create_collection(self, collection_name: str, schema: Optional[Dict] = None) -> None:
        """Create MongoDB collection"""
        if collection_name not in self.db.list_collection_names():
            if schema:
                self.db.create_collection(collection_name, validator={'$jsonSchema': schema})
            else:
                self.db.create_collection(collection_name)
            logger.info(f"Created collection: {collection_name}")
    
    def drop_collection(self, collection_name: str) -> None:
        """Drop MongoDB collection"""
        self.db[collection_name].drop()
        logger.info(f"Dropped collection: {collection_name}")
    
    def list_collections(self) -> List[str]:
        """List all MongoDB collections"""
        return self.db.list_collection_names()
    
    def insert_documents(self, collection: str, documents: List[Dict]) -> int:
        """Insert documents into MongoDB"""
        if not documents:
            return 0
        result = self.db[collection].insert_many(documents)
        logger.info(f"Inserted {len(result.inserted_ids)} documents into {collection}")
        return len(result.inserted_ids)
    
    def insert_one(self, collection: str, document: Dict) -> Any:
        """Insert single document into MongoDB"""
        result = self.db[collection].insert_one(document)
        return result.inserted_id
    
    def find_documents(self, collection: str, query: Optional[Dict] = None,
                      limit: int = 0, skip: int = 0) -> List[Dict]:
        """Query MongoDB documents"""
        if query is None:
            query = {}
        cursor = self.db[collection].find(query).skip(skip)
        if limit > 0:
            cursor = cursor.limit(limit)
        return list(cursor)
    
    def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        """Find single MongoDB document"""
        return self.db[collection].find_one(query)
    
    def count_documents(self, collection: str, query: Optional[Dict] = None) -> int:
        """Count MongoDB documents"""
        if query is None:
            query = {}
        return self.db[collection].count_documents(query)
    
    def update_documents(self, collection: str, query: Dict, update: Dict) -> int:
        """Update multiple MongoDB documents"""
        result = self.db[collection].update_many(query, {'$set': update})
        return result.modified_count
    
    def update_one(self, collection: str, query: Dict, update: Dict) -> bool:
        """Update single MongoDB document"""
        result = self.db[collection].update_one(query, {'$set': update})
        return result.modified_count > 0
    
    def delete_documents(self, collection: str, query: Dict) -> int:
        """Delete multiple MongoDB documents"""
        result = self.db[collection].delete_many(query)
        return result.deleted_count
    
    def delete_one(self, collection: str, query: Dict) -> bool:
        """Delete single MongoDB document"""
        result = self.db[collection].delete_one(query)
        return result.deleted_count > 0
    
    def bulk_write(self, collection: str, operations: List[Dict]) -> Dict:
        """Execute bulk write operations on MongoDB"""
        from pymongo import InsertOne, UpdateOne, DeleteOne
        
        mongo_ops = []
        for op in operations:
            if 'insert_one' in op:
                mongo_ops.append(InsertOne(op['insert_one']))
            elif 'update_one' in op:
                mongo_ops.append(UpdateOne(
                    op['update_one']['filter'],
                    {'$set': op['update_one']['update']}
                ))
            elif 'delete_one' in op:
                mongo_ops.append(DeleteOne(op['delete_one']))
        
        if mongo_ops:
            result = self.db[collection].bulk_write(mongo_ops)
            return {
                'inserted': result.inserted_count,
                'updated': result.modified_count,
                'deleted': result.deleted_count
            }
        return {'inserted': 0, 'updated': 0, 'deleted': 0}
    
    def create_index(self, collection: str, field_name: str, unique: bool = False) -> None:
        """Create index on MongoDB field"""
        self.db[collection].create_index([(field_name, 1)], unique=unique)
        logger.info(f"Created index on {collection}.{field_name}")
    
    def get_collection_stats(self, collection: str) -> Dict:
        """Get MongoDB collection statistics"""
        stats = self.db.command('collStats', collection)
        return {
            'count': stats.get('count', 0),
            'size': stats.get('size', 0),
            'avg_doc_size': stats.get('avgObjSize', 0),
            'indexes': len(stats.get('indexSizes', {}))
        }
    
    def mask_field(self, collection: str, field: str, mask_fn) -> int:
        """Apply masking function to MongoDB field"""
        docs = self.db[collection].find()
        masked_count = 0
        
        for doc in docs:
            if field in doc and doc[field]:
                masked_value = mask_fn(doc[field])
                self.db[collection].update_one(
                    {'_id': doc['_id']},
                    {'$set': {field: masked_value}}
                )
                masked_count += 1
        
        logger.info(f"Masked {masked_count} documents in {collection}.{field}")
        return masked_count
    
    def get_schema(self, collection: str, sample_size: int = 10) -> DocumentSchema:
        """Infer MongoDB collection schema"""
        from bson import ObjectId
        
        sample_docs = list(self.db[collection].find().limit(sample_size))
        
        if not sample_docs:
            return DocumentSchema(name=collection, fields={})
        
        # Merge field info from all samples
        field_info = {}
        all_field_names = set()
        
        for doc in sample_docs:
            all_field_names.update(doc.keys())
        
        for field_name in all_field_names:
            if field_name == '_id':
                continue
            
            types = set()
            nullable = False
            
            for doc in sample_docs:
                if field_name not in doc:
                    nullable = True
                else:
                    value = doc[field_name]
                    if isinstance(value, bool):
                        types.add('boolean')
                    elif isinstance(value, int):
                        types.add('integer')
                    elif isinstance(value, float):
                        types.add('float')
                    elif isinstance(value, str):
                        types.add('string')
                    elif isinstance(value, dict):
                        types.add('object')
                    elif isinstance(value, list):
                        types.add('array')
                    elif isinstance(value, ObjectId):
                        types.add('objectid')
            
            field_type = list(types)[0] if types else 'unknown'
            
            field_info[field_name] = FieldSchema(
                name=field_name,
                type=field_type,
                nullable=nullable
            )
        
        return DocumentSchema(name=collection, fields=field_info)


class PostgreSQLAdapter(DataAdapter):
    """PostgreSQL implementation of DataAdapter using psycopg2"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self, connection_string: str, **options) -> None:
        """Connect to PostgreSQL"""
        import psycopg2
        
        try:
            self.connection = psycopg2.connect(connection_string)
            self.cursor = self.connection.cursor()
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close PostgreSQL connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from PostgreSQL")
    
    def health_check(self) -> bool:
        """Verify PostgreSQL connectivity"""
        try:
            self.cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False
    
    def validate_connection(self) -> Tuple[bool, str]:
        """Validate PostgreSQL connection"""
        try:
            self.cursor.execute("SELECT version()")
            version = self.cursor.fetchone()[0]
            return True, f"Connected to {version}"
        except Exception as e:
            return False, f"PostgreSQL connection failed: {str(e)}"
    
    # ... implement remaining abstract methods for PostgreSQL ...
    
    def create_collection(self, collection_name: str, schema: Optional[Dict] = None) -> None:
        pass
    
    def drop_collection(self, collection_name: str) -> None:
        pass
    
    def list_collections(self) -> List[str]:
        pass
    
    def insert_documents(self, collection: str, documents: List[Dict]) -> int:
        pass
    
    def insert_one(self, collection: str, document: Dict) -> Any:
        pass
    
    def find_documents(self, collection: str, query: Optional[Dict] = None,
                      limit: int = 0, skip: int = 0) -> List[Dict]:
        pass
    
    def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        pass
    
    def count_documents(self, collection: str, query: Optional[Dict] = None) -> int:
        pass
    
    def update_documents(self, collection: str, query: Dict, update: Dict) -> int:
        pass
    
    def update_one(self, collection: str, query: Dict, update: Dict) -> bool:
        pass
    
    def delete_documents(self, collection: str, query: Dict) -> int:
        pass
    
    def delete_one(self, collection: str, query: Dict) -> bool:
        pass
    
    def bulk_write(self, collection: str, operations: List[Dict]) -> Dict:
        pass
    
    def create_index(self, collection: str, field_name: str, unique: bool = False) -> None:
        pass
    
    def get_collection_stats(self, collection: str) -> Dict:
        pass
    
    def mask_field(self, collection: str, field: str, mask_fn) -> int:
        pass
    
    def get_schema(self, collection: str, sample_size: int = 10) -> DocumentSchema:
        pass


# Factory function to get the right adapter
def get_adapter(database_type: str) -> DataAdapter:
    """
    Factory function to get database adapter.
    
    Args:
        database_type: 'mongodb', 'postgresql', 'mysql', etc.
    
    Returns:
        DataAdapter implementation
    """
    adapters = {
        'mongodb': MongoDBAdapter,
        'postgresql': PostgreSQLAdapter,
        # 'mysql': MySQLAdapter,
        # 'dynamodb': DynamoDBAdapter,
    }
    
    adapter_class = adapters.get(database_type.lower())
    if not adapter_class:
        raise ValueError(f"Unknown database type: {database_type}")
    
    return adapter_class()
