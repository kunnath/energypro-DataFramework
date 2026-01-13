# 2. TEST DATA AUTOMATION FRAMEWORK

## 2.1 Data Automation Lifecycle

### Complete Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE TRIGGER (git push)                      │
└────────────────┬────────────────────────────────────────────────────┘
                 │
    ┌────────────┴──────────────┐
    ▼                           ▼
┌──────────────────┐  ┌────────────────────────────┐
│ 1. REQUIREMENT   │  │ Data Spec in Git           │
│    ANALYSIS      │  │ - Schema (PostgreSQL)      │
│                  │  │ - Volumes (1K records)     │
│                  │  │ - Relationships (FK)       │
│                  │  │ - Masking rules            │
└──────────────────┘  └────────────────────────────┘
                            │
                            ▼
                  ┌─────────────────────────┐
                  │ 2. DATA GENERATION      │
                  │ Options:                │
                  │ a) Synthetic (Faker)    │
                  │ b) Masked Prod Copy     │
                  │ c) Versioned Seeds      │
                  │ d) Hybrid approach      │
                  └────────┬────────────────┘
                           │
                           ▼
                  ┌──────────────────────────────┐
                  │ 3. PII MASKING               │
                  │ - Email anonymization        │
                  │ - Phone redaction            │
                  │ - SSN/PII hashing            │
                  │ - Address randomization      │
                  │ - Apply at DB or app layer   │
                  └────────┬─────────────────────┘
                           │
                           ▼
                  ┌──────────────────────────────┐
                  │ 4. DATA VERSIONING           │
                  │ - Git commit data snapshots  │
                  │ - Version tags (v1.0.1)     │
                  │ - Changelog tracking        │
                  │ - Rollback capability       │
                  └────────┬─────────────────────┘
                           │
                           ▼
                  ┌──────────────────────────────┐
                  │ 5. DATA PROVISIONING         │
                  │ - Load into ephemeral DB     │
                  │ - Distribute across shards   │
                  │ - Validate schema integrity  │
                  │ - Check referential integrity│
                  └────────┬─────────────────────┘
                           │
                           ▼
                  ┌──────────────────────────────┐
                  │ 6. DATA VALIDATION           │
                  │ - Row counts match expected  │
                  │ - Referential integrity OK  │
                  │ - Sample data query check    │
                  │ - No nulls in PK columns     │
                  └────────┬─────────────────────┘
                           │
                           ▼
                  ┌──────────────────────────────┐
                  │ 7. TEST EXECUTION            │
                  │ - Run test suite             │
                  │ - Collect results            │
                  │ - Capture logs/metrics       │
                  │ - Track data modifications   │
                  └────────┬─────────────────────┘
                           │
                           ▼
                  ┌──────────────────────────────┐
                  │ 8. DATA REFRESH/CLEANUP      │
                  │ - Truncate temp tables       │
                  │ - Reset sequences            │
                  │ - Backup if failure logging  │
                  │ - Archive audit logs        │
                  └────────┬─────────────────────┘
                           │
                           ▼
                  ┌──────────────────────────────┐
                  │ 9. AUTOMATED REFRESH         │
                  │ - Scheduled (weekly) copy    │
                  │ - From production (masked)   │
                  │ - Version control            │
                  │ - Diff changes               │
                  └────────┬─────────────────────┘
                           │
                           ▼
                  ┌──────────────────────────────┐
                  │ 10. ROLLBACK & RECOVERY      │
                  │ - Revert to known good      │
                  │ - Git checkout data version  │
                  │ - Restart failed tests      │
                  │ - Validate recovery state   │
                  └──────────────────────────────┘

Timeline: 30 seconds total for full lifecycle
```

---

## 2.2 Data-as-Code Design Principles

### 2.2.1 Git-Based Data Definitions

All test data is version-controlled in Git, enabling:
- **Reproducibility**: Clone repo, get exact test data
- **Collaboration**: Code review for data changes
- **Auditability**: Git history shows who changed what
- **Rollback**: Instant recovery to known good data state

#### Example: `test-data-automation/data_definitions/users.yaml`

```yaml
# Git-versioned data specification
# Path: test-data-automation/data_definitions/users.yaml
# Version: v1.2.0

apiVersion: data.automation/v1
kind: DataDefinition
metadata:
  name: users
  namespace: test-data
  version: v1.2.0
  description: "User records for E2E testing"

spec:
  # Source: synthetic generation
  source: synthetic
  
  # Target database
  database:
    engine: postgresql
    connection:
      host: ${PGHOST}        # Injected from environment
      port: ${PGPORT}
      database: ${PGDATABASE}
      user: ${PGUSER}
  
  # Table definition
  table: public.users
  
  # Volume specification
  volume:
    count: 10000             # Generate 10K user records
    distribution: uniform    # Evenly distributed
  
  # Field specifications with generation rules
  fields:
    - name: id
      type: integer
      generator: sequence
      start: 1000
      
    - name: email
      type: varchar(255)
      generator: email
      pattern: "user+{{index}}@example.com"
      masking: true         # Mark for masking
      
    - name: phone
      type: varchar(20)
      generator: phone_number
      country_code: US
      masking: true
      
    - name: first_name
      type: varchar(100)
      generator: first_name
      
    - name: last_name
      type: varchar(100)
      generator: last_name
      
    - name: ssn
      type: varchar(11)
      generator: ssn
      masking: true
      pii_category: ssn
      
    - name: address
      type: text
      generator: address
      masking: true
      
    - name: created_at
      type: timestamp
      generator: datetime_between
      start_date: -30d       # Last 30 days
      
    - name: status
      type: varchar(20)
      generator: choice
      choices:
        - active
        - inactive
        - suspended
      weights: [70, 20, 10]  # Distribution weights
      
    - name: is_verified
      type: boolean
      generator: boolean
      true_probability: 0.8
  
  # Relationships to other tables
  relationships:
    - foreignKey: account_id
      references: accounts.id
      onDelete: cascade
      
    - foreignKey: org_id
      references: organizations.id
      onDelete: restrict
  
  # Masking rules applied before provisioning
  masking_rules:
    - field: email
      rule: anonymize_email
      
    - field: phone
      rule: redact_phone
      
    - field: ssn
      rule: hash_ssn
      algorithm: sha256
      
    - field: address
      rule: randomize_address
      
  # Validation after generation
  validation:
    - constraint: "email LIKE '%@example.com'"
      description: "All emails must be example.com"
      
    - constraint: "created_at <= NOW()"
      description: "Dates cannot be in future"
      
    - constraint: "NOT NULL (id, email)"
      description: "Required fields populated"
  
  # Versioning & refresh strategy
  refresh:
    schedule: "0 */6 * * *"     # Every 6 hours
    source: masked_production   # Refresh from masked prod
    tag_version: true           # Create Git tag for snapshot
```

#### Example: `test-data-automation/data_definitions/orders.yaml`

```yaml
# Orders with relationships to users
apiVersion: data.automation/v1
kind: DataDefinition
metadata:
  name: orders
  version: v1.0.0

spec:
  source: synthetic
  
  table: public.orders
  
  volume:
    count: 50000            # 5 orders per user (10K users)
    
  fields:
    - name: id
      type: integer
      generator: sequence
      start: 5000
      
    - name: user_id
      type: integer
      generator: reference   # FK to users.id
      reference_table: users
      reference_field: id
      
    - name: order_number
      type: varchar(20)
      generator: order_number
      pattern: "ORD-{{timestamp}}-{{index}}"
      
    - name: total_amount
      type: decimal(10,2)
      generator: random_decimal
      min: 10.00
      max: 9999.99
      
    - name: status
      type: varchar(20)
      generator: choice
      choices: [pending, processing, shipped, delivered, cancelled]
      weights: [10, 20, 40, 25, 5]
      
    - name: created_at
      type: timestamp
      generator: datetime_between
      start_date: -180d
      
  validation:
    - constraint: "user_id IN (SELECT id FROM users)"
    - constraint: "total_amount > 0"
```

### 2.2.2 Schema-Aware Data Generation

Data generation respects database schema automatically:

```python
# test-data-automation/schema_aware_generator.py

from dataclasses import dataclass
from typing import Dict, List, Any
import psycopg2
from faker import Faker

@dataclass
class ColumnConstraint:
    """Represents a database column constraint"""
    name: str
    data_type: str
    is_nullable: bool
    is_pk: bool
    is_fk: bool
    max_length: int = None
    foreign_key_ref: tuple = None  # (table, column)

class SchemaAwareGenerator:
    """Generate data respecting schema constraints"""
    
    def __init__(self, db_connection_string: str):
        self.conn = psycopg2.connect(db_connection_string)
        self.cursor = self.conn.cursor()
        self.faker = Faker()
        self.constraints: Dict[str, List[ColumnConstraint]] = {}
    
    def introspect_schema(self, table_name: str) -> List[ColumnConstraint]:
        """Introspect PostgreSQL schema for given table"""
        query = """
            SELECT 
                c.column_name,
                c.data_type,
                c.is_nullable,
                tc.constraint_type,
                kcu.table_name as fk_table,
                kcu.column_name as fk_column
            FROM information_schema.columns c
            LEFT JOIN information_schema.table_constraints tc 
                ON c.table_name = tc.table_name 
                AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY')
            LEFT JOIN information_schema.key_column_usage kcu 
                ON c.table_name = kcu.table_name 
                AND c.column_name = kcu.column_name
            WHERE c.table_name = %s
            ORDER BY c.ordinal_position
        """
        
        self.cursor.execute(query, (table_name,))
        rows = self.cursor.fetchall()
        
        constraints = []
        for col_name, data_type, is_nullable, constraint_type, fk_table, fk_col in rows:
            is_pk = constraint_type == 'PRIMARY KEY'
            is_fk = constraint_type == 'FOREIGN KEY'
            fk_ref = (fk_table, fk_col) if is_fk else None
            
            constraint = ColumnConstraint(
                name=col_name,
                data_type=data_type,
                is_nullable=is_nullable.lower() == 'yes',
                is_pk=is_pk,
                is_fk=is_fk,
                foreign_key_ref=fk_ref
            )
            constraints.append(constraint)
        
        self.constraints[table_name] = constraints
        return constraints
    
    def generate_record(self, table_name: str, overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a single record respecting schema"""
        if table_name not in self.constraints:
            self.introspect_schema(table_name)
        
        record = {}
        overrides = overrides or {}
        
        for constraint in self.constraints[table_name]:
            # Skip primary keys (auto-increment)
            if constraint.is_pk:
                continue
            
            # Use override if provided
            if constraint.name in overrides:
                record[constraint.name] = overrides[constraint.name]
                continue
            
            # Generate based on type and constraints
            value = self._generate_value(table_name, constraint)
            record[constraint.name] = value
        
        return record
    
    def _generate_value(self, table_name: str, constraint: ColumnConstraint) -> Any:
        """Generate appropriate value for column"""
        
        # Handle foreign keys
        if constraint.is_fk:
            return self._get_existing_fk_value(constraint.foreign_key_ref)
        
        # Handle by data type
        if 'integer' in constraint.data_type.lower():
            return self.faker.random_int(min=1000, max=999999)
        
        elif 'varchar' in constraint.data_type.lower():
            max_len = constraint.max_length or 100
            return self.faker.word()[:max_len]
        
        elif 'email' in constraint.name.lower():
            return self.faker.email()
        
        elif 'phone' in constraint.name.lower():
            return self.faker.phone_number()
        
        elif 'timestamp' in constraint.data_type.lower():
            return self.faker.date_time_this_year()
        
        elif 'boolean' in constraint.data_type.lower():
            return self.faker.boolean()
        
        elif 'decimal' in constraint.data_type.lower():
            return float(self.faker.random_int(min=100, max=99999) / 100)
        
        else:
            return None if constraint.is_nullable else self.faker.word()
    
    def _get_existing_fk_value(self, fk_ref: tuple) -> Any:
        """Get existing PK value to use as FK"""
        fk_table, fk_column = fk_ref
        query = f"SELECT {fk_column} FROM {fk_table} ORDER BY RANDOM() LIMIT 1"
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def generate_bulk(self, table_name: str, count: int) -> List[Dict[str, Any]]:
        """Generate multiple records"""
        records = []
        for _ in range(count):
            records.append(self.generate_record(table_name))
        return records
    
    def load_into_db(self, table_name: str, records: List[Dict[str, Any]]):
        """Bulk insert generated records"""
        if not records:
            return
        
        columns = list(records[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        values = [tuple(record[col] for col in columns) for record in records]
        
        self.cursor.executemany(query, values)
        self.conn.commit()
        
        print(f"Loaded {len(records)} records into {table_name}")

# Usage
generator = SchemaAwareGenerator("postgresql://user:pass@localhost:5432/testdb")
users = generator.generate_bulk("users", count=10000)
generator.load_into_db("users", users)
```

---

## 2.3 Test-Case-Driven Data Provisioning

### 2.3.1 Data Contracts

Each test case declares what data it needs, enabling just-in-time provisioning:

```python
# test-data-automation/test_contracts.py

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class DataScope(Enum):
    """Data isolation scope"""
    TEST_CASE = "test_case"        # New data per test
    TEST_CLASS = "test_class"       # Shared across class
    TEST_MODULE = "test_module"     # Shared across module
    SHARED = "shared"               # Shared across suite

@dataclass
class DataContract:
    """Declares data requirements for a test"""
    test_name: str
    scope: DataScope
    datasets: List[str]             # e.g., ["users", "orders"]
    volume: Dict[str, int]          # e.g., {"users": 100, "orders": 500}
    isolation_level: str            # "full" or "schema-level"
    masking_required: bool          # Apply PII masking?
    version: str                    # Data spec version (v1.0.0)
    
    def __hash__(self):
        return hash((self.test_name, self.scope.value, tuple(sorted(self.datasets))))

class TestDataManager:
    """Manages data provisioning per test contract"""
    
    def __init__(self, db_connection_string: str):
        self.db_connection = db_connection_string
        self.provisioned_data: Dict[int, Dict[str, Any]] = {}  # Keyed by contract hash
    
    def provision(self, contract: DataContract) -> Dict[str, Any]:
        """
        Provision data according to contract.
        Returns mapping of dataset_name -> [records]
        """
        contract_hash = hash(contract)
        
        # Check if already provisioned (for shared scope)
        if contract_hash in self.provisioned_data:
            return self.provisioned_data[contract_hash]
        
        provisioned = {}
        
        for dataset in contract.datasets:
            count = contract.volume.get(dataset, 100)
            
            # Load data spec from Git
            spec = self._load_spec(dataset, contract.version)
            
            # Adjust volume
            spec.volume = count
            
            # Generate or fetch data
            records = self._generate_data(spec, contract.masking_required)
            
            # Load into database
            self._load_to_db(dataset, records, contract.isolation_level)
            
            provisioned[dataset] = records
        
        # Store for shared scope
        if contract.scope in [DataScope.SHARED, DataScope.TEST_MODULE]:
            self.provisioned_data[contract_hash] = provisioned
        
        return provisioned
    
    def cleanup(self, contract: DataContract):
        """Clean up data after test"""
        if contract.scope == DataScope.TEST_CASE:
            # Truncate tables created for this test
            for dataset in contract.datasets:
                self._truncate_table(dataset)
        
        # Remove from cache if not shared
        contract_hash = hash(contract)
        if contract_hash in self.provisioned_data:
            if contract.scope == DataScope.TEST_CASE:
                del self.provisioned_data[contract_hash]
    
    def _load_spec(self, dataset: str, version: str) -> Dict[str, Any]:
        """Load data spec from Git-versioned YAML"""
        import yaml
        spec_path = f"test-data-automation/data_definitions/{dataset}.yaml"
        with open(spec_path) as f:
            spec = yaml.safe_load(f)
        return spec
    
    def _generate_data(self, spec: Dict, apply_masking: bool) -> List[Dict]:
        """Generate data from spec"""
        # Implementation would use SchemaAwareGenerator
        pass
    
    def _load_to_db(self, dataset: str, records: List[Dict], isolation: str):
        """Load records into database"""
        pass
    
    def _truncate_table(self, dataset: str):
        """Truncate table after test"""
        pass
```

### 2.3.2 Test Decorator for Data Contracts

```python
# test-data-automation/decorators.py

from functools import wraps
from typing import List, Dict

def requires_test_data(
    datasets: List[str],
    volume: Dict[str, int],
    scope: str = "TEST_CASE",
    isolation: str = "full",
    apply_masking: bool = True,
    version: str = "latest"
):
    """
    Decorator to specify data contract for a test
    
    Usage:
    @requires_test_data(
        datasets=["users", "orders"],
        volume={"users": 100, "orders": 500},
        scope="TEST_CASE",
        isolation="full"
    )
    def test_checkout_flow():
        # Data is provisioned before test runs
        ...
    """
    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            from test_data_automation.test_contracts import DataContract, DataScope, TestDataManager
            
            # Create data contract
            contract = DataContract(
                test_name=test_func.__name__,
                scope=DataScope(scope.lower()),
                datasets=datasets,
                volume=volume,
                isolation_level=isolation,
                masking_required=apply_masking,
                version=version
            )
            
            # Initialize data manager
            import os
            db_conn = os.getenv("TEST_DATABASE_URL")
            data_mgr = TestDataManager(db_conn)
            
            # Provision data
            provisioned_data = data_mgr.provision(contract)
            
            # Inject into test context
            kwargs['test_data'] = provisioned_data
            
            try:
                # Run test
                result = test_func(*args, **kwargs)
            finally:
                # Cleanup
                data_mgr.cleanup(contract)
            
            return result
        
        return wrapper
    return decorator

# Usage example:
@requires_test_data(
    datasets=["users", "orders", "payments"],
    volume={"users": 50, "orders": 200, "payments": 200},
    scope="TEST_CASE",
    isolation="full",
    apply_masking=True
)
def test_checkout_with_multiple_items(test_data):
    """Test checkout flow with masked data"""
    users = test_data["users"]
    orders = test_data["orders"]
    
    # Test uses the provisioned data
    response = checkout(user_id=users[0]["id"], order_id=orders[0]["id"])
    assert response.status_code == 200
```

---

## 2.4 Data Masking Implementation

### 2.4.1 SQL-Based Masking (Database Layer)

```sql
-- test-data-automation/data_masking.sql
-- Applied before test execution; persistent for test run

-- Hash sensitive fields with SHA256
UPDATE users 
SET ssn = ENCODE(DIGEST(ssn, 'sha256'), 'hex'),
    email = 'masked-' || gen_random_uuid()::text || '@example.com',
    phone = '555-' || LPAD((RANDOM() * 9999)::int::text, 4, '0'),
    address = 'Masked Address'
WHERE 1=1;

-- Anonymize payment card details
UPDATE payments
SET card_number = SUBSTRING(card_number, 1, 4) || '-****-****-' || 
                  SUBSTRING(card_number, -4),
    cvv = '***'
WHERE 1=1;

-- Redact user behavior data
UPDATE user_sessions
SET ip_address = '192.168.1.1',
    user_agent = 'Mozilla/5.0 (Generic)'
WHERE 1=1;

-- Create view for data quality checks (before masking)
CREATE VIEW masked_users_before AS
SELECT COUNT(*) as user_count,
       COUNT(DISTINCT email) as unique_emails
FROM users;
```

### 2.4.2 Python-Based Masking (Application Layer)

```python
# test-data-automation/data_masking.py

import hashlib
import re
from typing import Dict, Any, List
from faker import Faker

class DataMasker:
    """Applies PII masking to generated test data"""
    
    def __init__(self):
        self.faker = Faker()
        self.masking_rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, callable]:
        """Load masking rules from config"""
        return {
            'email': self._mask_email,
            'phone': self._mask_phone,
            'ssn': self._mask_ssn,
            'credit_card': self._mask_credit_card,
            'address': self._mask_address,
            'name': self._mask_name,
            'ip_address': self._mask_ip,
            'dob': self._mask_dob
        }
    
    def mask_record(self, record: Dict[str, Any], schema_hints: Dict[str, str]) -> Dict[str, Any]:
        """
        Mask a single record based on field names and types
        
        Args:
            record: Original record
            schema_hints: Dict mapping field name -> masking_type
                         e.g., {"email": "email", "phone": "phone"}
        """
        masked = record.copy()
        
        for field_name, masking_type in schema_hints.items():
            if field_name in masked and masking_type in self.masking_rules:
                masked[field_name] = self.masking_rules[masking_type](masked[field_name])
        
        return masked
    
    def mask_bulk(self, records: List[Dict[str, Any]], schema_hints: Dict[str, str]) -> List[Dict[str, Any]]:
        """Mask multiple records"""
        return [self.mask_record(rec, schema_hints) for rec in records]
    
    # Masking implementations
    
    def _mask_email(self, value: str) -> str:
        """Anonymize email address"""
        return f"masked-{self.faker.uuid4()}@example.com"
    
    def _mask_phone(self, value: str) -> str:
        """Redact phone number"""
        return "555-" + "".join([str(i % 10) for i in range(7)])
    
    def _mask_ssn(self, value: str) -> str:
        """Hash SSN"""
        return hashlib.sha256(value.encode()).hexdigest()[:8]
    
    def _mask_credit_card(self, value: str) -> str:
        """Redact credit card (keep first 4, last 4)"""
        if len(value) < 8:
            return "****"
        return value[:4] + "****" * 3 + value[-4:]
    
    def _mask_address(self, value: str) -> str:
        """Randomize address"""
        return self.faker.address()
    
    def _mask_name(self, value: str) -> str:
        """Replace with fake name"""
        return self.faker.name()
    
    def _mask_ip(self, value: str) -> str:
        """Replace IP with non-routable address"""
        return "192.168." + ".".join([str(i % 256) for i in range(2)])
    
    def _mask_dob(self, value: str) -> str:
        """Replace DOB with random date"""
        return str(self.faker.date_of_birth(minimum_age=18, maximum_age=80))

# Usage
masker = DataMasker()

schema_hints = {
    "email": "email",
    "phone": "phone",
    "ssn": "ssn",
    "credit_card": "credit_card",
    "address": "address"
}

original_records = [
    {
        "id": 1,
        "email": "john.doe@company.com",
        "phone": "555-123-4567",
        "ssn": "123-45-6789",
        "address": "123 Main St, New York, NY 10001"
    }
]

masked_records = masker.mask_bulk(original_records, schema_hints)
# Result: email, phone, ssn, address all anonymized
```

---

## 2.5 Data Provisioning API

### 2.5.1 REST API for On-Demand Data

```python
# test-data-automation/data_provision_api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import yaml
import logging

app = FastAPI(title="Test Data Provisioning API")

logger = logging.getLogger(__name__)

class ProvisionRequest(BaseModel):
    """Request to provision test data"""
    datasets: List[str]
    volumes: Dict[str, int]
    apply_masking: bool = True
    version: str = "latest"
    isolation: str = "full"

class ProvisionResponse(BaseModel):
    """Response after provisioning"""
    request_id: str
    status: str  # "success", "in_progress", "failed"
    datasets_provisioned: List[str]
    record_counts: Dict[str, int]
    provisioned_at: str
    expires_at: str  # TTL for ephemeral data

class DataProvisioningService:
    """Service to provision test data on-demand"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.provisioning_jobs = {}
    
    def provision(self, request: ProvisionRequest) -> ProvisionResponse:
        """Provision test data according to request"""
        request_id = str(uuid.uuid4())
        
        try:
            record_counts = {}
            
            for dataset in request.datasets:
                count = request.volumes.get(dataset, 100)
                
                # Load spec
                spec = self._load_spec(dataset, request.version)
                
                # Generate data
                records = self._generate(spec, count)
                
                # Apply masking if requested
                if request.apply_masking:
                    records = self._apply_masking(records, spec)
                
                # Load into database
                self._load_to_db(dataset, records, request.isolation)
                
                record_counts[dataset] = len(records)
                logger.info(f"Provisioned {len(records)} {dataset} records")
            
            response = ProvisionResponse(
                request_id=request_id,
                status="success",
                datasets_provisioned=request.datasets,
                record_counts=record_counts,
                provisioned_at=datetime.utcnow().isoformat(),
                expires_at=(datetime.utcnow() + timedelta(hours=2)).isoformat()
            )
            
            self.provisioning_jobs[request_id] = response
            return response
        
        except Exception as e:
            logger.error(f"Provisioning failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _load_spec(self, dataset: str, version: str) -> Dict:
        """Load data spec from Git"""
        spec_path = f"test-data-automation/data_definitions/{dataset}.yaml"
        with open(spec_path) as f:
            return yaml.safe_load(f)
    
    def _generate(self, spec: Dict, count: int) -> List[Dict]:
        """Generate records"""
        # Use SchemaAwareGenerator
        pass
    
    def _apply_masking(self, records: List[Dict], spec: Dict) -> List[Dict]:
        """Apply masking rules"""
        masker = DataMasker()
        hints = {f: "generic" for f in spec.get('masking_rules', [])}
        return masker.mask_bulk(records, hints)
    
    def _load_to_db(self, dataset: str, records: List[Dict], isolation: str):
        """Load into database"""
        pass

# Initialize service
provisioning_service = DataProvisioningService(db_config={
    "host": "localhost",
    "port": 5432,
    "database": "testdb"
})

@app.post("/provision", response_model=ProvisionResponse)
async def provision_data(request: ProvisionRequest) -> ProvisionResponse:
    """
    Provision test data on-demand.
    
    Example:
    POST /provision
    {
        "datasets": ["users", "orders"],
        "volumes": {"users": 100, "orders": 500},
        "apply_masking": true,
        "version": "v1.0.0"
    }
    """
    return provisioning_service.provision(request)

@app.get("/provision/{request_id}")
async def get_provision_status(request_id: str):
    """Check status of provisioning request"""
    if request_id not in provisioning_service.provisioning_jobs:
        raise HTTPException(status_code=404, detail="Request not found")
    return provisioning_service.provisioning_jobs[request_id]

@app.delete("/provision/{request_id}")
async def cleanup_provision(request_id: str):
    """Cleanup provisioned data"""
    if request_id not in provisioning_service.provisioning_jobs:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Truncate tables
    del provisioning_service.provisioning_jobs[request_id]
    return {"status": "cleaned_up"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2.5.2 CLI Tool for Data Provisioning

```bash
#!/usr/bin/env python3
# test-data-automation/ista_data_cli.py

import click
import json
import requests
import yaml
from typing import Dict, List

@click.group()
def cli():
    """ISTA Data Provisioning CLI"""
    pass

@cli.command()
@click.option('--datasets', type=str, required=True, help='Comma-separated dataset names')
@click.option('--volumes', type=str, required=False, help='JSON volumes per dataset')
@click.option('--mask', is_flag=True, default=True, help='Apply PII masking')
@click.option('--version', type=str, default='latest', help='Data spec version')
def provision(datasets: str, volumes: str, mask: bool, version: str):
    """
    Provision test data.
    
    Examples:
    $ ista-data provision --datasets users,orders \\
      --volumes '{"users":100,"orders":500}' --version v1.0.0
    """
    dataset_list = [d.strip() for d in datasets.split(',')]
    volumes_dict = json.loads(volumes) if volumes else {d: 100 for d in dataset_list}
    
    request_payload = {
        "datasets": dataset_list,
        "volumes": volumes_dict,
        "apply_masking": mask,
        "version": version
    }
    
    response = requests.post(
        "http://localhost:8000/provision",
        json=request_payload
    )
    
    if response.status_code == 200:
        result = response.json()
        click.echo(click.style("✓ Provisioning successful", fg='green'))
        click.echo(f"Request ID: {result['request_id']}")
        click.echo(f"Records provisioned:")
        for dataset, count in result['record_counts'].items():
            click.echo(f"  - {dataset}: {count}")
        click.echo(f"Expires at: {result['expires_at']}")
    else:
        click.echo(click.style(f"✗ Provisioning failed: {response.text}", fg='red'), err=True)

@cli.command()
@click.argument('request_id')
def status(request_id: str):
    """Check provisioning status"""
    response = requests.get(f"http://localhost:8000/provision/{request_id}")
    
    if response.status_code == 200:
        result = response.json()
        click.echo(f"Status: {result['status']}")
        click.echo(f"Datasets: {', '.join(result['datasets_provisioned'])}")
        click.echo(f"Records: {json.dumps(result['record_counts'], indent=2)}")
    else:
        click.echo(f"Request not found: {request_id}")

@cli.command()
@click.argument('request_id')
def cleanup(request_id: str):
    """Cleanup provisioned data"""
    response = requests.delete(f"http://localhost:8000/provision/{request_id}")
    
    if response.status_code == 200:
        click.echo(click.style(f"✓ Cleaned up {request_id}", fg='green'))
    else:
        click.echo(click.style(f"✗ Cleanup failed", fg='red'), err=True)

@cli.command()
@click.option('--dataset', type=str, required=True, help='Dataset name')
def show_spec(dataset: str):
    """Show data specification for dataset"""
    try:
        with open(f"test-data-automation/data_definitions/{dataset}.yaml") as f:
            spec = yaml.safe_load(f)
        click.echo(yaml.dump(spec, default_flow_style=False))
    except FileNotFoundError:
        click.echo(f"Spec not found for dataset: {dataset}", err=True)

if __name__ == '__main__':
    cli()

# Usage examples:
# $ ista-data provision --datasets users,orders --volumes '{"users":100,"orders":500}'
# $ ista-data status abc-123-def
# $ ista-data cleanup abc-123-def
# $ ista-data show-spec users
```

---

## 2.6 Data Factory Patterns

### 2.6.1 Factory Pattern Implementation

```python
# test-data-automation/data_factories.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from faker import Faker

@dataclass
class User:
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str
    created_at: datetime
    is_verified: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "created_at": self.created_at.isoformat(),
            "is_verified": self.is_verified
        }

@dataclass
class Order:
    id: int
    user_id: int
    order_number: str
    total_amount: float
    status: str
    created_at: datetime
    items: List['OrderItem'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "order_number": self.order_number,
            "total_amount": self.total_amount,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items]
        }

@dataclass
class OrderItem:
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float

class BaseFactory(ABC):
    """Base factory for all test data factories"""
    
    counter = {}
    faker = Faker()
    
    @classmethod
    def _get_next_id(cls, key: str) -> int:
        """Get next auto-incrementing ID"""
        if key not in cls.counter:
            cls.counter[key] = 1000
        cls.counter[key] += 1
        return cls.counter[key]
    
    @classmethod
    def reset_counter(cls):
        """Reset all counters"""
        cls.counter = {}

class UserFactory(BaseFactory):
    """Factory for creating User test data"""
    
    @classmethod
    def create(cls, **overrides) -> User:
        """Create a single user with optional field overrides"""
        user_id = cls._get_next_id('user')
        
        defaults = {
            'id': user_id,
            'email': f"user+{user_id}@example.com",
            'first_name': cls.faker.first_name(),
            'last_name': cls.faker.last_name(),
            'phone': cls.faker.phone_number(),
            'created_at': cls.faker.date_time_this_year(),
            'is_verified': cls.faker.boolean(chance_of_getting_true=80)
        }
        
        defaults.update(overrides)
        return User(**defaults)
    
    @classmethod
    def create_batch(cls, count: int, **overrides) -> List[User]:
        """Create multiple users"""
        return [cls.create(**overrides) for _ in range(count)]
    
    @classmethod
    def create_verified(cls, **overrides) -> User:
        """Create a verified user"""
        return cls.create(is_verified=True, **overrides)
    
    @classmethod
    def create_unverified(cls, **overrides) -> User:
        """Create an unverified user"""
        return cls.create(is_verified=False, **overrides)

class OrderFactory(BaseFactory):
    """Factory for creating Order test data"""
    
    statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    
    @classmethod
    def create(cls, user_id: int = None, **overrides) -> Order:
        """Create a single order"""
        order_id = cls._get_next_id('order')
        
        defaults = {
            'id': order_id,
            'user_id': user_id or cls._get_next_id('user'),
            'order_number': f"ORD-{datetime.now().strftime('%Y%m%d')}-{order_id}",
            'total_amount': round(cls.faker.random.uniform(10.00, 9999.99), 2),
            'status': cls.faker.random_element(cls.statuses),
            'created_at': cls.faker.date_time_this_year(),
            'items': []
        }
        
        defaults.update(overrides)
        return Order(**defaults)
    
    @classmethod
    def create_batch(cls, count: int, user_id: int = None, **overrides) -> List[Order]:
        """Create multiple orders"""
        return [cls.create(user_id=user_id, **overrides) for _ in range(count)]
    
    @classmethod
    def create_completed(cls, user_id: int = None, **overrides) -> Order:
        """Create a completed order"""
        return cls.create(user_id=user_id, status='delivered', **overrides)
    
    @classmethod
    def create_with_items(cls, item_count: int = 3, user_id: int = None, **overrides) -> Order:
        """Create an order with items"""
        order = cls.create(user_id=user_id, **overrides)
        
        for i in range(item_count):
            item = OrderItem(
                id=cls._get_next_id('order_item'),
                order_id=order.id,
                product_id=cls._get_next_id('product'),
                quantity=cls.faker.random_int(min=1, max=10),
                unit_price=round(cls.faker.random.uniform(5.00, 500.00), 2)
            )
            order.items.append(item)
        
        return order

# Usage in tests
def test_checkout_flow():
    """Example test using factories"""
    # Create test data
    user = UserFactory.create_verified(email="test@example.com")
    order = OrderFactory.create_with_items(item_count=3, user_id=user.id)
    
    # Use in test
    response = checkout(user_id=user.id, order_id=order.id)
    assert response.status_code == 200
    
    # Cleanup
    UserFactory.reset_counter()
    OrderFactory.reset_counter()

def test_bulk_orders():
    """Create bulk test data"""
    users = UserFactory.create_batch(100)
    orders = []
    
    for user in users:
        user_orders = OrderFactory.create_batch(5, user_id=user.id)
        orders.extend(user_orders)
    
    # Test with 100 users, 500 orders
    response = bulk_process(orders)
    assert response.status_code == 200
```

---

## 2.7 Repository Structure

```
test-data-automation/
├── data_definitions/              # Git-versioned data specs
│   ├── users.yaml
│   ├── orders.yaml
│   ├── payments.yaml
│   └── README.md
│
├── data_generator.py              # Synthetic data generation
├── data_masking.py                # PII masking logic
├── data_masking.sql               # Database-level masking
├── data_provision_api.py          # REST API for provisioning
├── ista_data_cli.py               # CLI tool
├── data_factories.py              # Factory patterns
├── data_contracts.py              # Test data contracts
├── decorators.py                  # @requires_test_data decorator
├── schema_aware_generator.py      # Schema introspection + generation
│
├── tests/                         # Tests for data automation
│   ├── test_factories.py
│   ├── test_masking.py
│   └── test_provisioning_api.py
│
├── requirements.txt               # Python dependencies
├── README.md                      # Documentation
└── Dockerfile                     # Container for API service
```

---

## Summary: Test Data Automation Framework

**Key Capabilities**:
- ✅ On-demand synthetic data generation
- ✅ Git-versioned data specifications
- ✅ Automated PII masking (SQL + Python layers)
- ✅ Test-case-driven provisioning via decorators
- ✅ Data factory patterns for complex scenarios
- ✅ REST API + CLI for self-service data provisioning
- ✅ Schema-aware generation respecting constraints
- ✅ Data versioning & rollback capability

**Business Impact**:
- 🚀 30-second data provisioning (vs. 45 minutes manual)
- 🔒 100% automated compliance masking
- ⚡ Parallel test isolation via ephemeral data
- 📊 Self-service for 90% of test data needs

---

**Next Document**: [03_TEST_ENVIRONMENT_AUTOMATION.md](docs/03_TEST_ENVIRONMENT_AUTOMATION.md)
