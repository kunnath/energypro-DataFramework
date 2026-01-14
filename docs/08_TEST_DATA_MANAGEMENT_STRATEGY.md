# 8.  TEST DATA MANAGEMENT STRATEGY ACROSS QA/PROD/PREPROD/DEV ENVIRONMENTS

**Version:** 1.0  
**Date:** January 2026  
**Audience:** Engineering Teams, QA, DevOps, Platform Engineers  
**Purpose:** Comprehensive guide for implementing test data management across development, testing, and production-like environments

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Core Principles](#core-principles)
3. [Data Management Architecture](#data-management-architecture)
4. [Data Lifecycle Management](#data-lifecycle-management)
5. [Environment-Specific Strategies](#environment-specific-strategies)
6. [Data Quality & Consistency](#data-quality--consistency)
7. [Security & Compliance](#security--compliance)
8. [Tooling & Automation](#tooling--automation)
9. [Implementation Checklist](#implementation-checklist)
10. [Best Practices & Common Pitfalls](#best-practices--common-pitfalls)

---

## Executive Summary

### The Challenge

Manual test data management across environments creates:
- **Operational overhead**: 45+ minutes per environment setup
- **Test flakiness**: 15-20% of failures are environment-related, not code-related
- **Data isolation issues**: Shared test data causes test interdependencies
- **Compliance risk**: Manual PII handling → breach exposure
- **Cost overruns**: $400K+ annually in wasted infrastructure
- **Slow feedback loops**: 4+ hours to get environments ready

### The Solution

A **layered, automated test data management strategy** that:
- ✅ Provisions environments in **< 2 minutes** (vs 45 min)
- ✅ Eliminates shared data contention → **isolated, parallel test execution**
- ✅ Ensures data consistency via **version control & immutable seeds**
- ✅ Automates PII masking → **compliance-grade data handling**
- ✅ Reduces costs by **80%** through ephemeral, automated infrastructure
- ✅ Provides **instant developer feedback** via local test environments

### Key Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Environment Setup Time** | 45 min | < 2 min | **95% faster** |
| **Test Flakiness (Environment-Related)** | 15% | < 2% | **87% reduction** |
| **Annual Infra Costs** | $400K | $80K | **80% savings** |
| **Concurrent Test Jobs** | 10 | 50+ | **5x scalability** |
| **PII Masking Coverage** | Manual (error-prone) | 100% automated | **Zero manual risk** |
| **Developer Setup Time** | 2 hours | 5 min | **24x faster** |

---

## Core Principles

### 1️⃣ **Deterministic & Reproducible**

Every test run must start with identical test data state, ensuring consistent results across environments.

```
Principle: Version Control Everything
├── Schema definitions (Git)
├── Test data seeds (Git or versioned artifacts)
├── Data specifications (YAML config in Git)
└── Masking policies (Git-tracked)

Result: "Run tests on Commit A from any environment → Same results"
```

**Implementation**:
- Store data schemas and definitions in Git
- Version test data snapshots with semantic versioning (v1.0.0, v1.0.1)
- Use immutable test data releases
- Tag data versions alongside code versions

### 2️⃣ **Data Isolation & No Shared State**

Each test execution must operate on independent, disposable data to prevent cross-test pollution.

```
BEFORE (Shared Data):
  Test A: CREATE user "john@example.com"
  Test B: DELETE user "john@example.com" (expecting it exists)
  Test B FAILS (john is gone)
  Test A & B are interdependent ❌

AFTER (Isolated Data):
  Test A: [Fresh Data Set A] → CREATE/MODIFY/DELETE
  Test B: [Fresh Data Set B] → CREATE/MODIFY/DELETE
  Test A & B are independent ✅ Can run in parallel
```

**Implementation**:
- Provision fresh database per test suite execution
- Use database snapshots or in-memory databases (SQLite, Redis) for unit tests
- Implement test data factories for per-test setup
- Clean up after test execution (no state leakage)

### 3️⃣ **Compliance & Security-First**

PII and sensitive data must be automatically handled to meet regulatory requirements.

```
Data Classification:
├── 🔴 Personally Identifiable Information (PII)
│   ├── Email addresses
│   ├── Phone numbers
│   ├── Social Security Numbers / Tax IDs
│   ├── Names (in some contexts)
│   └── Physical addresses
├── 🟡 Sensitive Business Data
│   ├── Credit card numbers
│   ├── API keys / secrets
│   ├── Internal transaction IDs
│   └── Customer health records
└── 🟢 Non-Sensitive
    ├── Product names
    ├── Public demographic data
    └── Published reviews
```

**Implementation**:
- Classify data fields by sensitivity level
- Define masking/redaction rules per classification
- Automate masking at data generation or integration point
- Audit all data access with immutable logs
- Never log PII; sanitize error messages

### 4️⃣ **Environment Parity with Intentional Differences**

Test environments mirror production structure but with intentional simplifications for speed.

```
Parity Levels:

Level 1 (Local Dev):
  ├── Single-node database (vs distributed)
  ├── 100 test records (vs millions)
  ├── Synchronous operations (vs async queues)
  └── No external API calls (vs mocked)
  📊 Setup time: 30 seconds, Scope: 1 service

Level 2 (CI/CD Pipeline):
  ├── Docker containerized database (vs cloud-managed)
  ├── 1K-10K test records (vs millions)
  ├── Full async patterns (tests verify behavior)
  └── Mocked external services
  📊 Setup time: 60 seconds, Scope: Full integration

Level 3 (Staging-Like):
  ├── Multi-container orchestration (vs kubernetes)
  ├── 100K records (vs millions)
  ├── Real async patterns with test messages
  └── Real external services (or production-like stubs)
  📊 Setup time: 120 seconds, Scope: Full production replica

Level 4 (Production):
  ├── Full kubernetes cluster
  ├── Millions of records
  ├── All async patterns
  └── Real external integrations
  📊 Setup time: varies, Scope: Live customer data (masked)
```

**Implementation**:
- Use environment variables to switch behavior
- Run same test suite across levels 1-3
- Create level-specific data fixtures
- Document expected behavior differences

### 5️⃣ **Automation Over Manual Effort**

Minimize human intervention in data provisioning, masking, and cleanup.

```
Automation Coverage:

Data Generation:
  ├── ✅ Synthetic data from factories
  ├── ✅ Masked production data copies
  ├── ✅ Versioned seed snapshots
  └── ✅ Batch generation with progress tracking

PII Handling:
  ├── ✅ Automatic field detection
  ├── ✅ Hashing, redaction, anonymization
  ├── ✅ Audit logging (who accessed what)
  └── ✅ Compliance reporting

Lifecycle:
  ├── ✅ Provision on demand (API/CLI)
  ├── ✅ Health checks before test execution
  ├── ✅ Auto-cleanup after test completion
  └── ✅ Rollback to previous state on failure
```

---

## Data Management Architecture

### Layered Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│              Consumer Layer (Tests, Developers)                │
│  Unit Tests | Integration Tests | E2E Tests | Local Dev       │
└────────────────────────────────────────────────────────────────┘
                              ▲
┌────────────────────────────────────────────────────────────────┐
│         Interface Layer (APIs, CLIs, Configuration)            │
│  REST API | CLI Tools | Environment Config | IaC Templates    │
└────────────────────────────────────────────────────────────────┘
                              ▲
┌────────────────────────────────────────────────────────────────┐
│            Provisioning Layer (Orchestration)                  │
│  Data Generation | Seeding | Masking | Validation | Health    │
└────────────────────────────────────────────────────────────────┘
                              ▲
┌────────────────────────────────────────────────────────────────┐
│          Storage Layer (Databases & Artifacts)                 │
│  MongoDB | PostgreSQL | Redis | S3 | Git Repos               │
└────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Consumer Layer
- **Unit Tests**: In-memory or SQLite databases
- **Integration Tests**: Docker containers with test data
- **E2E Tests**: Multi-container environments with full stacks
- **Local Development**: Docker Compose for instant setup

#### 2. Interface Layer

**REST API**
```
POST /api/v1/test-data/provision
  └─ Request: { environment, dataset, count }
  └─ Response: { status, endpoint, healthcheck_url }

POST /api/v1/test-data/cleanup
  └─ Request: { environment, execution_id }
  └─ Response: { status, cleanup_time }

GET /api/v1/test-data/status/{execution_id}
  └─ Response: { ready, health_checks, sample_data }
```

**CLI Tool**
```bash
$ data-cli provision --env dev --dataset movies --count 1000
$ data-cli show --collection users --limit 5
$ data-cli cleanup --execution-id abc123
$ data-cli health check
$ data-cli export --format json --output backup.json
```

**Configuration**
```yaml
# data-spec.yaml
environments:
  local:
    volumes: 100
    masking: aggressive
  ci:
    volumes: 1000
    masking: standard
  staging:
    volumes: 100000
    masking: standard
  
datasets:
  movies:
    factory: MovieFactory
    relationships:
      - { foreign_key: user_id, collection: users }
  
masking_policies:
  email: anonymize
  phone: redact
  ssn: hash
```

#### 3. Provisioning Layer

**Data Generation Engine**
- Accept requests for test data
- Create data using factories (synthetic) or templates (masked production)
- Validate against schema
- Store generated data
- Return metadata (count, size, record IDs)

**Validation Engine**
- Schema validation (all required fields present, correct types)
- Relationship validation (foreign keys exist)
- Data consistency checks (e.g., dates in logical order)
- Performance baselines (e.g., index creation time)

**Masking Engine**
- Detect PII fields using classification metadata
- Apply transformations (hash, redact, anonymize)
- Maintain referential integrity (hashed emails must be consistent)
- Audit transformations (log what was masked, by whom, when)

**Health Check Engine**
- Connectivity tests (can reach database)
- Schema validation (tables/collections exist with correct structure)
- Sample query tests (basic CRUD operations work)
- Performance baseline checks (response times acceptable)
- Data readiness (data fully loaded, indexes created)

#### 4. Storage Layer

**Version Control (Git)**
- Schema definitions
- Data specifications
- Masking policies
- Test data snapshots (small datasets)
- Changelog and migration history

**Databases**
- Development: Local containers
- Testing: Ephemeral cloud instances (auto-destroyed)
- Staging: Persistent but refreshable
- Production: Never used for test data (only masked copies)

**Artifacts**
- Data exports (JSON, CSV, SQL dumps)
- Backups and snapshots
- Performance baselines
- Compliance reports

---

## Data Lifecycle Management

### Complete Data Journey

```
┌──────────────────────────────────────────────────────────────────────┐
│ 1. SPECIFICATION                                                     │
│   ├─ Define schema: fields, types, constraints                      │
│   ├─ Define volumes: how many records per dataset                   │
│   ├─ Define relationships: foreign keys, references                 │
│   ├─ Define masking: which fields need PII protection               │
│   └─ Store in Git version control                                   │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│ 2. GENERATION                                                        │
│   ├─ Synthetic approach: Use Faker libraries for realistic data     │
│   ├─ Template approach: Copy production data and mask               │
│   ├─ Hybrid: Mix of synthetic + masked production                   │
│   ├─ Versioned: Create reproducible data snapshots                  │
│   └─ Batched: Parallel generation for large datasets                │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│ 3. MASKING & SANITIZATION                                           │
│   ├─ Field-level: Hash emails, redact SSNs, anonymize names        │
│   ├─ Referential: Maintain FK consistency (same masked value = same │
│   ├─ Audit: Log all masking operations                              │
│   ├─ Compliance: Ensure GDPR, CCPA, HIPAA requirements             │
│   └─ Validation: Verify masking didn't break data integrity         │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│ 4. VERSIONING & TAGGING                                             │
│   ├─ Version format: v1.0.0 (semantic versioning)                   │
│   ├─ Git commits: Track who changed what and when                   │
│   ├─ Changelog: Document breaking changes                           │
│   ├─ Artifacts: Store immutable data snapshots                      │
│   └─ Rollback: Easy revert to previous versions                     │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│ 5. DISTRIBUTION                                                      │
│   ├─ API endpoints: Request data programmatically                   │
│   ├─ CLI tools: Quick provisioning from command line                │
│   ├─ Database dumps: SQL/JSON for manual import                     │
│   ├─ Docker volumes: Pre-populated containers                       │
│   └─ Caching: Reuse generated data across test runs                 │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│ 6. DEPLOYMENT TO ENVIRONMENTS                                       │
│   ├─ Local: Load into Docker Compose container                      │
│   ├─ CI: Spin up ephemeral database, seed data                      │
│   ├─ Staging: Refresh persistent DB with versioned snapshot         │
│   ├─ Production: Never; use masked copy in separate account         │
│   └─ Validation: Health checks before test execution                │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│ 7. USAGE & MONITORING                                               │
│   ├─ Metrics: Track data growth, access patterns                    │
│   ├─ Auditing: Log all reads/writes for compliance                  │
│   ├─ Performance: Monitor query times, index usage                  │
│   ├─ Alerting: Notify if data becomes stale or corrupted            │
│   └─ Feedback: Developers report if data insufficient               │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│ 8. CLEANUP & ARCHIVAL                                               │
│   ├─ Ephemeral environments: Auto-destroy after tests complete      │
│   ├─ Persistent environments: Refresh on schedule or manual trigger  │
│   ├─ Archives: Long-term storage for audit/compliance               │
│   ├─ Compliance: Data deletion per GDPR right to forget            │
│   └─ Metrics: Track cleanup success and failure rates               │
└──────────────────────────────────────────────────────────────────────┘
```

### State Transitions & Workflows

#### Workflow A: Local Developer Workflow
```
1. Developer clones repo
2. Runs: docker-compose up (includes pre-seeded DB)
3. Runs: data-cli provision --env local --dataset movies
4. Database ready with test data (5 seconds)
5. Developer runs tests locally
6. Tests pass (or dev debugs)
7. Developer pushes to Git
8. CI/CD pipeline runs with same tests
```

#### Workflow B: CI/CD Pipeline Workflow
```
1. Git push triggers CI job
2. Infrastructure provisioned (Terraform or docker-compose)
3. Test data seeded via API or CLI
4. Health checks pass
5. Test suite runs against fresh environment
6. Environment torn down (auto-cleanup)
7. Results reported (pass/fail/coverage)
8. Artifacts archived (logs, coverage reports)
```

#### Workflow C: Staging Refresh Workflow
```
1. On schedule (nightly) or manual trigger
2. Fetch latest data specification from Git
3. Generate/retrieve masked production copy
4. Validate data integrity
5. Swap old data with new (atomic transaction)
6. Run smoke tests against refreshed staging
7. Notify teams of refresh status
8. Archive old data for compliance
```

---

## Environment-Specific Strategies

### 1. Local Development Environment

**Goals**: Minimal setup, instant feedback, no external dependencies

**Implementation**:
```yaml
Docker Compose Stack:
  services:
    database:
      image: mongo:latest
      volumes:
        - ./test-data/seed.json:/seed.json
      entrypoint: >
        sh -c "mongod & sleep 5 && mongoimport 
        --uri mongodb://localhost:27017/testdb 
        --file /seed.json"
    api:
      build: .
      depends_on:
        - database
      environment:
        DATABASE_URL: mongodb://database:27017/testdb
    redis:
      image: redis:latest

volumes:
  mongodb:
```

**Data Strategy**:
- 🟢 Pre-seeded snapshot (git-tracked, small)
- 🟢 In-memory SQLite for unit tests
- 🟢 Factories for test-specific data creation
- 🔴 ❌ No integration with production systems

**Provisioning Time**: < 30 seconds
**Data Volume**: 100-1000 records per collection

**CLI Example**:
```bash
# Setup
docker-compose up -d
data-cli provision --env local --dataset users --count 100

# Verify
data-cli health check
data-cli show --collection users --limit 5

# Cleanup
docker-compose down
```

### 2. CI/CD Pipeline Environments

**Goals**: Fast, isolated, parallel execution, deterministic results

**Implementation**:
```yaml
GitHub Actions / GitLab CI Example:

stages:
  provision:
    script:
      - docker run -d --name mongodb mongo:latest
      - sleep 5
      - data-cli provision --env ci --dataset all
      - data-cli health check
    timeout: 120s
  
  test:
    script:
      - npm test
      - pytest tests/
    depends_on:
      - provision
    parallel:
      matrix:
        - test_suite: unit
        - test_suite: integration
        - test_suite: api
  
  cleanup:
    script:
      - docker stop mongodb
      - docker rm mongodb
    always: true
```

**Data Strategy**:
- 🟢 Ephemeral containers (1 per test job)
- 🟢 Versioned data snapshots (immutable)
- 🟢 Factories for variant generation (edge cases)
- 🔴 ❌ No persistent state between runs

**Provisioning Time**: < 60 seconds
**Data Volume**: 1K-10K records per collection
**Parallelism**: 50+ concurrent environments

**Features**:
- ✅ Deterministic results (same data every run)
- ✅ Zero test interdependencies
- ✅ Cost-effective (destroyed after tests)
- ✅ Full audit trail (container logs)

### 3. Staging-Like Environments

**Goals**: Realistic simulation of production, team visibility, longer lifecycle

**Implementation**:
```yaml
Kubernetes / Cloud Deployment:

StatefulSets:
  mongodb-staging:
    replicas: 3
    volumeClaimTemplates:
      - size: 100Gi
    
    initContainers:
      - name: data-provisioner
        image: data-provisioner:latest
        args:
          - provision
          - --env staging
          - --dataset all
          - --replicate true

ConfigMaps:
  data-spec: <contents of data specifications YAML>
  masking-policies: <contents of masking rules>

CronJobs:
  refresh-data:
    schedule: "0 2 * * *"  # 2 AM daily
    jobTemplate:
      spec:
        containers:
          - name: provisioner
            image: data-provisioner:latest
            args: [refresh, --env staging]
```

**Data Strategy**:
- 🟡 Persistent database (survives pod restarts)
- 🟡 Regular refresh cycles (daily/weekly)
- 🟡 Mix of synthetic + masked production data
- 🟢 Full compliance & audit logging
- ✅ Team access (read-only for most users)

**Provisioning Time**: 2-5 minutes
**Data Volume**: 100K-1M records
**Refresh Frequency**: Daily or manual on-demand

**Features**:
- ✅ Long-lived (supports exploratory testing)
- ✅ Realistic scale and relationships
- ✅ Performance testing baseline
- ✅ Team collaboration environment
- ✅ Compliance data handling

### 4. Production (Masked Data Only)

**Goals**: Zero-risk testing of real data patterns, compliance-grade security

**Implementation**:
```
CRITICAL: Never use real production databases for testing

Instead:
1. Export production data to isolated account
2. Mask all PII using automated tools
3. Create read-only database replica
4. All access logged and audited
5. Data deleted after retention period
6. Compliance officer sign-off required

Example: AWS Approach
├─ Production Account
│  └─ [Real Customer Data - LOCKED]
├─ Test Data Account
│  ├─ Daily snapshot copy (automated)
│  ├─ Automated masking pipeline
│  ├─ Read-only database clone
│  └─ Encryption at rest & in transit
├─ Compliance Logging
│  ├─ All access logged
│  ├─ Cloudtrail audit trail
│  └─ Access revocation after 30 days
```

**Data Strategy**:
- 🔴 Always masked
- 🔴 Separate AWS account
- 🔴 Immutable audit logs
- 🔴 Automated expiration
- 🔴 Encryption everywhere
- ✅ Production-representative

**Access Model**:
```
Who Can Access?
├─ QA Engineers: Read-only (select all)
├─ Developers: Read-only (dev-related queries only)
├─ DevOps: Full access (for troubleshooting)
├─ Product: Never
├─ Analysts: Read-only (aggregated, anonymized)

How Long?
├─ Active session: 8 hours
├─ Standing access: 7 days
├─ Audit logs: 1 year
├─ Data deleted: 30 days
```

---

## Data Quality & Consistency

### Schema Validation Framework

```yaml
# schema-validation.yaml
collections:
  users:
    strict: true  # No extra fields allowed
    fields:
      _id:
        type: ObjectId
        required: true
      name:
        type: string
        required: true
        pattern: "^[A-Za-z ]+$"
      email:
        type: string
        required: true
        pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      phone:
        type: string
        required: true
        pattern: "^\\+?[1-9]\\d{1,14}$"  # E.164 format
      created_at:
        type: date
        required: true
        constraint: "< now()"
      age:
        type: number
        required: false
        constraint: "> 0 AND < 150"
    
    indexes:
      - { fields: [email], unique: true, name: email_idx }
      - { fields: [created_at], name: created_at_idx }
    
    relationships:
      - foreign_key: user_id
        references: movies.user_id

movies:
  strict: false  # Allow additional fields
  fields:
    _id:
      type: ObjectId
      required: true
    title:
      type: string
      required: true
    year:
      type: number
      required: true
      constraint: ">= 1900 AND <= 2100"
    user_id:
      type: ObjectId
      required: true
      foreign_key: users._id
```

### Validation Workflow

```
┌──────────────────────────────────────┐
│ Data Generation                      │
└────────────┬─────────────────────────┘
             │
┌────────────▼──────────────────────────┐
│ 1. Schema Validation                  │
│  ├─ All required fields present?      │
│  ├─ Correct data types?               │
│  ├─ Pattern matching (regex)?         │
│  └─ Constraints satisfied?            │
└────────────┬───────────────────────────┘
             │
        FAIL? → Log & reject
             │
┌────────────▼──────────────────────────┐
│ 2. Relationship Validation            │
│  ├─ Foreign keys exist?               │
│  ├─ Back-references present?          │
│  ├─ Referential integrity intact?     │
│  └─ No orphaned records?              │
└────────────┬───────────────────────────┘
             │
        FAIL? → Log & rollback
             │
┌────────────▼──────────────────────────┐
│ 3. Data Consistency Check             │
│  ├─ Logical order (dates)?            │
│  ├─ Dependencies satisfied?           │
│  ├─ Aggregates match (count)?         │
│  └─ No duplicates (unless allowed)?   │
└────────────┬───────────────────────────┘
             │
        FAIL? → Alert & investigate
             │
┌────────────▼──────────────────────────┐
│ 4. Performance Baseline               │
│  ├─ Index creation time < 30s?        │
│  ├─ Sample query time < 100ms?        │
│  ├─ Data loading time < 60s?          │
│  └─ Memory usage reasonable?          │
└────────────┬───────────────────────────┘
             │
        OK ✅ Data Ready for Testing
```

### Data Consistency Patterns

#### Pattern 1: Immutable Seeds
```
Once generated, test data version is fixed.
If tests need different data → create new version.

Versions:
├─ v1.0.0: Initial release (100 users, 1000 movies)
├─ v1.0.1: Bug fix (corrected date format)
├─ v1.1.0: Added edge cases (v1.0.0 + extreme values)
├─ v2.0.0: New schema (breaking change)

Git History:
commit abc123: "Release v1.1.0 with edge cases"
  files: data-specs/users-v1.1.0.yaml
         data-factory/MovieFactory.py
```

#### Pattern 2: Deterministic Generation
```
Same seed + same factory = identical data every time

# Pseudo-code example
class MovieFactory:
  def __init__(self, random_seed: int):
    self.faker = Faker()
    self.faker.seed_instance(random_seed)
    self.random = Random(random_seed)
  
  def generate_movies(count: int):
    # All movies generated are identical across runs
    # due to fixed random seed
    for i in range(count):
      yield self.create()

# Usage:
factory = MovieFactory(random_seed=12345)
movies_run_1 = factory.generate_movies(100)  # Same 100 movies
movies_run_2 = factory.generate_movies(100)  # Same 100 movies ✅
```

#### Pattern 3: Relationship Consistency
```
Foreign key integrity across generations

Problem: Generate 100 users, 1000 movies
  - Some movie_user_ids reference non-existent users
  - Referential integrity broken ❌

Solution: Coordinated generation
  1. Generate 100 users → collect their IDs
  2. Generate 1000 movies → select user IDs from step 1
  3. Validate all movies reference valid users ✅

Implementation:
class MovieFactory:
  def __init__(self, user_ids: List[ObjectId]):
    self.valid_user_ids = user_ids
  
  def create(self):
    return {
      "_id": ObjectId(),
      "user_id": random.choice(self.valid_user_ids),  # Always valid
      ...
    }
```

---

## Security & Compliance

### PII Classification & Handling

```
CRITICAL: Implement at application layer, not just database layer

Classification Hierarchy:

🔴 HIGHLY SENSITIVE (PII)
├─ Full names (in many contexts)
├─ Email addresses
├─ Phone numbers
├─ Social Security Numbers / Tax IDs
├─ Driver license numbers
├─ Passport numbers
├─ Credit/debit card numbers
├─ Banking information (account #, routing #)
├─ Medical records
├─ Biometric data

🟡 SENSITIVE (SPI - Sensitive Personal Information)
├─ IP addresses
├─ Geolocation data
├─ Device identifiers (IMEI, MAC)
├─ Session tokens
├─ API keys
├─ Internal user IDs (in some systems)
├─ Pseudonymized data (if re-identifiable)

🟢 NON-SENSITIVE
├─ Publicly available data
├─ Product names & descriptions
├─ Published reviews & ratings
├─ Aggregated statistics
├─ Anonymized data (truly irreversible)
```

### PII Masking Strategies

#### Strategy 1: Hashing
```
Use case: Email addresses (values must be consistent)

Problem: If Test A checks "john@example.com" exists
         Test B must see the same hashed value

Solution: Hash with salt (but same salt for reproducibility)

Implementation:
import hashlib

HASH_SALT = "fixed_test_salt_12345"

def hash_email(email: str) -> str:
  input_str = email + HASH_SALT
  return hashlib.sha256(input_str.encode()).hexdigest()

# Result:
hash_email("john@example.com")  # "a1b2c3d4..." (deterministic)
hash_email("john@example.com")  # "a1b2c3d4..." (same!)
hash_email("jane@example.com")  # "x9y8z7w6..." (different)
```

#### Strategy 2: Redaction
```
Use case: Phone numbers (just hide them)

Problem: Tests don't need actual phone numbers
Solution: Replace with dummy value

Implementation:
def redact_phone(phone: str) -> str:
  return "+1-555-0000"

# Result:
{
  "user_id": "abc123",
  "name": "John Doe",
  "phone": "+1-555-0000"  # All phones same (safe!)
}
```

#### Strategy 3: Anonymization
```
Use case: Names (replace with fake names)

Problem: Real names expose identity
Solution: Replace with realistic but non-real names (Faker)

Implementation:
from faker import Faker

fake = Faker()
fake.seed_instance(12345)

def anonymize_name(original_name: str) -> str:
  # Don't use original name (privacy risk)
  # Use Faker for realistic replacement
  return fake.name()

# Result:
anonymize_name("John Smith")    # "Jane Doe" (fictional)
anonymize_name("Mary Johnson")  # "Robert Wilson" (fictional)
```

#### Strategy 4: Aggregation
```
Use case: Sensitive metrics (show patterns, not raw data)

Problem: Raw transaction amounts expose financial data
Solution: Report ranges/aggregates instead

Implementation:
def anonymize_amounts(transactions: List[dict]) -> dict:
  amounts = [t['amount'] for t in transactions]
  return {
    "total": sum(amounts),
    "average": sum(amounts) / len(amounts),
    "count": len(amounts),
    "min": min(amounts),
    "max": max(amounts),
    # Raw amounts NOT included
  }
```

### Masking Configuration

```yaml
# masking-policies.yaml
policies:
  default:
    strategy: hash
    salt: default_salt_12345
  
  pii:
    fields:
      - email
      - phone
      - ssn
      - credit_card
      - full_name
    
    email:
      strategy: hash
      salt: email_salt_9876
    
    phone:
      strategy: redact
      replacement: "+1-555-0000"
    
    ssn:
      strategy: hash
      salt: ssn_salt_5555
    
    full_name:
      strategy: anonymize
      faker_provider: name
    
    credit_card:
      strategy: hash
      show_last_4: true  # xxxx-xxxx-xxxx-1234
  
  audit:
    log_masking_operations: true
    include_user_id: true
    include_timestamp: true
    encryption: AES-256

regulatory_compliance:
  GDPR:
    right_to_deletion: true
    right_to_access: true
    data_retention_days: 30
  
  CCPA:
    opt_out_tracking: true
    personal_info_disclosure: required
  
  HIPAA:
    phi_fields: [medical_record_id, diagnosis, medication]
    encryption: required
    audit_logging: required
```

### Audit & Compliance Logging

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "event": "data_masking",
  "operation": "provision_dataset",
  "environment": "staging",
  "dataset_id": "ds_abc123",
  "user_id": "user_xyz789",
  "actions": [
    {
      "action": "hash",
      "field": "email",
      "record_count": 1000,
      "status": "success"
    },
    {
      "action": "redact",
      "field": "phone",
      "record_count": 1000,
      "status": "success"
    },
    {
      "action": "anonymize",
      "field": "full_name",
      "record_count": 1000,
      "status": "success"
    }
  ],
  "validation": {
    "referential_integrity": "passed",
    "schema_validation": "passed",
    "data_consistency": "passed"
  },
  "compliance_check": {
    "gdpr_compliant": true,
    "ccpa_compliant": true,
    "audit_trail_complete": true
  }
}
```

---

## Tooling & Automation

### Essential Tools & Technologies

#### 1. Data Factory Framework

| Framework | Language | Use Case | Pros | Cons |
|-----------|----------|----------|------|------|
| **Factory Boy** | Python | Django models | Easy ORM integration | Python-only |
| **Faker** | Python/JS/Ruby | Realistic data | Excellent customization | No schema validation |
| **ModelFaker** | Multiple | Cross-platform | Language agnostic | Complex setup |
| **Custom Factories** | Any | Precise control | Total flexibility | More code |

**Recommendation**: Build custom factories + Faker for flexibility

```python
# mongo_factories.py example
from faker import Faker
from pymongo import MongoClient

class BaseFactory:
  def __init__(self, client: MongoClient, db_name: str):
    self.client = client
    self.db = client[db_name]
    self.faker = Faker()
    self.faker.seed_instance(12345)

class UserFactory(BaseFactory):
  def create(self, **overrides):
    doc = {
      "_id": ObjectId(),
      "email": self.faker.email(),
      "name": self.faker.name(),
      "phone": self.faker.phone_number(),
      "created_at": datetime.now(),
      **overrides
    }
    # Mask PII
    doc["email"] = hash_email(doc["email"])
    doc["phone"] = redact_phone(doc["phone"])
    return self.db.users.insert_one(doc)
```

#### 2. Data Specification Language

**YAML** for simplicity and Git-friendliness:

```yaml
# data-spec.yaml
version: 1.0
datasets:
  users:
    factory: UserFactory
    volume: 1000
    fields:
      - name: email
        type: string
        required: true
        masked: hash
      - name: phone
        type: string
        required: true
        masked: redact
      - name: age
        type: number
        required: false
        constraint: "> 0 AND < 150"
  
  movies:
    factory: MovieFactory
    volume: 5000
    relationships:
      - user_id -> users._id (foreign key)
```

#### 3. CLI Tool Architecture

```python
# data-cli.py (Click-based CLI)
import click
from provisioner import DataProvisioner

@click.group()
def cli():
  """Data provisioning CLI for test environments"""
  pass

@cli.command()
@click.option('--env', required=True)
@click.option('--dataset', required=True)
@click.option('--count', type=int, default=None)
def provision(env: str, dataset: str, count: int):
  """Provision test data"""
  provisioner = DataProvisioner(env)
  result = provisioner.provision(dataset, count)
  click.echo(f"✅ Provisioned {result['count']} records")

@cli.command()
@click.option('--execution-id', required=True)
def cleanup(execution_id: str):
  """Clean up test data"""
  provisioner = DataProvisioner()
  provisioner.cleanup(execution_id)
  click.echo(f"✅ Cleaned up {execution_id}")

@cli.command()
def health():
  """Check environment health"""
  provisioner = DataProvisioner()
  status = provisioner.health_check()
  click.echo(json.dumps(status, indent=2))

if __name__ == '__main__':
  cli()
```

#### 4. API Layer for CI/CD Integration

```python
# FastAPI-based REST API
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ProvisionRequest(BaseModel):
  environment: str
  dataset: str
  count: Optional[int] = None

class ProvisionResponse(BaseModel):
  execution_id: str
  status: str
  database_url: str
  health_check_url: str

@app.post("/api/v1/provision")
async def provision(req: ProvisionRequest) -> ProvisionResponse:
  provisioner = DataProvisioner(req.environment)
  result = provisioner.provision(req.dataset, req.count)
  return ProvisionResponse(**result)

@app.post("/api/v1/cleanup/{execution_id}")
async def cleanup(execution_id: str):
  provisioner = DataProvisioner()
  provisioner.cleanup(execution_id)
  return {"status": "success"}

@app.get("/api/v1/health/{execution_id}")
async def health(execution_id: str):
  provisioner = DataProvisioner()
  return provisioner.health_check(execution_id)
```

### Infrastructure Automation

#### Docker Compose for Local Dev

```yaml
# docker-compose.yml
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: test_mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: password
    volumes:
      - ./test-data/seed.json:/seed.json
      - mongo_data:/data/db
    healthcheck:
      test: ["CMD", "mongo", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - test-network

  data-provisioner:
    build: .
    depends_on:
      mongodb:
        condition: service_healthy
    environment:
      MONGO_URI: mongodb://root:password@mongodb:27017/testdb
      ENVIRONMENT: local
    volumes:
      - ./test-data-automation:/app
    networks:
      - test-network
    command: >
      sh -c "python -m pip install -e . &&
             data-cli health check &&
             data-cli provision --env local --dataset all"

  api:
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      - mongodb
      - data-provisioner
    environment:
      MONGO_URI: mongodb://root:password@mongodb:27017/testdb
    ports:
      - "8000:8000"
    networks:
      - test-network

volumes:
  mongo_data:

networks:
  test-network:
    driver: bridge
```

#### Kubernetes for Staging

```yaml
# k8s-manifest.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: data-spec
data:
  data-spec.yaml: |
    version: 1.0
    datasets:
      users:
        factory: UserFactory
        volume: 100000

---
apiVersion: batch/v1
kind: Job
metadata:
  name: data-provisioner
spec:
  template:
    spec:
      containers:
      - name: provisioner
        image: myregistry/data-provisioner:latest
        env:
        - name: MONGO_URI
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: uri
        - name: ENVIRONMENT
          value: staging
        volumeMounts:
        - name: data-spec
          mountPath: /config
      volumes:
      - name: data-spec
        configMap:
          name: data-spec
      restartPolicy: Never
  backoffLimit: 3

---
apiVersion: v1
kind: Service
metadata:
  name: provisioner-api
spec:
  selector:
    app: provisioner-api
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: LoadBalancer
```

---

## Implementation Checklist

### Phase 1: Foundation (Weeks 1-2)

- [ ] **Define data specifications**
  - [ ] Schema for each entity (users, orders, products, etc.)
  - [ ] Volume requirements per environment
  - [ ] Relationship definitions (foreign keys)
  - [ ] Store in Git repo as YAML

- [ ] **Classify sensitive data**
  - [ ] Audit all fields for PII
  - [ ] Document classification (🔴 sensitive, 🟡 moderate, 🟢 public)
  - [ ] Create masking-policies.yaml

- [ ] **Create base factory framework**
  - [ ] BaseFactory class
  - [ ] Integration with Faker
  - [ ] Error handling & logging
  - [ ] Unit tests for factories

### Phase 2: Local Development (Weeks 3-4)

- [ ] **Build Docker Compose stack**
  - [ ] Database service
  - [ ] Pre-seeded volumes
  - [ ] Health checks
  - [ ] Networking configuration

- [ ] **Implement CLI tool**
  - [ ] `provision` command
  - [ ] `cleanup` command
  - [ ] `health` command
  - [ ] `show` command for data inspection

- [ ] **Create per-entity factories**
  - [ ] UserFactory
  - [ ] ProductFactory
  - [ ] OrderFactory
  - [ ] (and others per your domain)

### Phase 3: CI/CD Integration (Weeks 5-6)

- [ ] **Implement REST API**
  - [ ] POST /provision
  - [ ] POST /cleanup
  - [ ] GET /health
  - [ ] API documentation

- [ ] **Integrate with CI/CD pipeline**
  - [ ] GitHub Actions / GitLab CI integration
  - [ ] Environment provisioning step
  - [ ] Health check validation
  - [ ] Auto-cleanup on completion

- [ ] **Add data versioning**
  - [ ] Semantic version tagging
  - [ ] Changelog management
  - [ ] Rollback procedures
  - [ ] Git tagging automation

### Phase 4: Production Readiness (Weeks 7-8)

- [ ] **Compliance & auditing**
  - [ ] Audit logging infrastructure
  - [ ] Compliance report generation
  - [ ] Data retention policies
  - [ ] Access control enforcement

- [ ] **Testing & validation**
  - [ ] Load testing (large datasets)
  - [ ] Performance benchmarking
  - [ ] Security scanning
  - [ ] Compliance verification

- [ ] **Documentation & training**
  - [ ] Developer guide
  - [ ] Operations runbook
  - [ ] Troubleshooting guide
  - [ ] Video tutorials

- [ ] **Monitoring & alerting**
  - [ ] Provisioning time metrics
  - [ ] Success/failure rates
  - [ ] Data quality alerts
  - [ ] PagerDuty integration

---

## Best Practices & Common Pitfalls

### ✅ Best Practices

#### 1. **Version Everything in Git**
```
❌ Bad: Store binary database dumps outside version control
✅ Good: YAML specs + factory code in Git with semantic versioning
```

#### 2. **Make Data Deterministic**
```
❌ Bad: Generate random data each time (flaky tests)
✅ Good: Fixed random seeds (Faker.seed_instance(12345))
```

#### 3. **Isolate Data Per Test**
```
❌ Bad: Shared database for all tests
✅ Good: Fresh DB per test job (Docker container)
```

#### 4. **Automate PII Masking**
```
❌ Bad: Manual review and masking (error-prone)
✅ Good: Field-level masking rules + automated application
```

#### 5. **Validate Referential Integrity**
```
❌ Bad: Generate users and movies independently
✅ Good: Collect user IDs, pass to movie factory for FK validation
```

#### 6. **Document Schema & Relationships**
```
❌ Bad: Implicit assumptions about data structure
✅ Good: Explicit YAML schema with constraints and relationships
```

#### 7. **Enable Fast Feedback**
```
❌ Bad: 45 min setup time before first test
✅ Good: docker-compose up → 30 seconds → ready to test
```

#### 8. **Audit All Data Access**
```
❌ Bad: No visibility into who accessed what test data
✅ Good: Immutable audit logs with user_id, timestamp, operation
```

### 🔴 Common Pitfalls & Fixes

#### Pitfall 1: Shared Test Data Causing Flakiness

**Symptom**: Tests pass in isolation but fail together (race condition)

```python
# ❌ WRONG: Shared data
@pytest.fixture(scope="session")
def users():
  return create_users()  # Created once, shared by all tests

def test_update_user(users):
  user = users[0]
  update_user(user.id, name="Alice")
  assert user.name == "Alice"

def test_delete_user(users):
  user = users[0]
  delete_user(user.id)  # Deletes Alice!
  assert user_exists(user.id) == False

# Tests fail if run in wrong order ❌

# ✅ CORRECT: Isolated data
@pytest.fixture
def user():  # function scope, not session
  return create_user()  # Fresh user per test

def test_update_user(user):
  update_user(user.id, name="Alice")
  assert user.name == "Alice"

def test_delete_user(user):  # Different user instance
  delete_user(user.id)
  assert user_exists(user.id) == False

# Both tests pass independently ✅
```

**Fix**:
- Use `@pytest.fixture` (function scope) instead of `@pytest.fixture(scope="session")`
- Provision fresh database per test job
- Implement factory pattern for per-test setup

#### Pitfall 2: Non-Deterministic Data Generation

**Symptom**: Same test produces different results across runs (debugging nightmare)

```python
# ❌ WRONG: Random seed not fixed
class UserFactory:
  def build(self):
    return {
      "name": faker.name(),  # Changes every time!
      "email": faker.email()  # Changes every time!
    }

# Scenario:
# Run 1: {"name": "John", "email": "john@example.com"}
# Run 2: {"name": "Jane", "email": "jane@example.com"}
# Tests fail inconsistently ❌

# ✅ CORRECT: Fixed seed for reproducibility
class UserFactory:
  def __init__(self, seed: int = 12345):
    self.faker = Faker()
    self.faker.seed_instance(seed)
  
  def build(self):
    return {
      "name": self.faker.name(),  # Always "Barbara Rogers" (same seed)
      "email": self.faker.email()  # Always "wperez@example.org"
    }

# Scenario:
# Run 1: {"name": "Barbara Rogers", "email": "wperez@example.org"}
# Run 2: {"name": "Barbara Rogers", "email": "wperez@example.org"}
# Tests pass consistently ✅
```

**Fix**:
- Use Faker.seed_instance() with fixed seed
- Store seed in version control
- Document deterministic data structure

#### Pitfall 3: Exposing PII in Test Data

**Symptom**: Real customer emails/phone numbers in test logs (compliance violation)

```json
# ❌ WRONG: Raw PII in test data
{
  "user_id": "abc123",
  "email": "john.smith@realemail.com",  // Real email!
  "phone": "+1-555-1234",               // Real phone!
  "ssn": "123-45-6789"                  // Real SSN!
}

// These fields appear in logs, test reports, etc. ❌
// GDPR/CCPA violation!

// ✅ CORRECT: PII masked
{
  "user_id": "abc123",
  "email": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",  // Hashed
  "phone": "+1-555-0000",                      // Redacted
  "ssn": "123456789abc123def456g"              // Hashed
}

// Safe to appear in logs/reports ✅
```

**Fix**:
- Classify all fields as PII/sensitive/public
- Apply masking at factory layer
- Audit masking operations
- Never commit real customer data to Git

#### Pitfall 4: Broken Referential Integrity

**Symptom**: Foreign key violations, orphaned records

```python
# ❌ WRONG: Independent generation
users = UserFactory().create_batch(100)
movies = MovieFactory().create_batch(1000)
# 500 movies may reference non-existent user IDs ❌

# ✅ CORRECT: Coordinated generation
user_ids = UserFactory().create_batch(100)  # Collect IDs
movies = MovieFactory(user_ids).create_batch(1000)
# All movies reference valid users ✅

# Implementation:
class MovieFactory:
  def __init__(self, valid_user_ids: List[ObjectId]):
    self.valid_user_ids = valid_user_ids
  
  def build(self):
    return {
      "user_id": random.choice(self.valid_user_ids),  # Guaranteed valid
      ...
    }
```

**Fix**:
- Generate parent entities first
- Pass valid IDs to child factories
- Validate referential integrity in tests
- Use database constraints (UNIQUE, FOREIGN KEY)

#### Pitfall 5: Environment-Specific Data Inconsistency

**Symptom**: Tests pass locally but fail in CI (different data)

```python
# ❌ WRONG: Environment-specific data
@pytest.fixture
def test_data():
  if os.getenv("ENV") == "local":
    return create_small_dataset()  # 100 records
  else:
    return create_large_dataset()  # 10000 records
  # Same tests, different data → inconsistent results ❌

# ✅ CORRECT: Identical data across environments
@pytest.fixture
def test_data():
  # Same data everywhere
  return DataFactory(seed=12345, volume=1000).create_batch()
  # Tests see same data locally, CI, staging ✅
```

**Fix**:
- Use identical data specifications across environments
- Only vary infrastructure size, not data structure
- Use YAML data-spec as source of truth
- Validate data after provisioning

#### Pitfall 6: No Audit Trail (Compliance Nightmare)

**Symptom**: "Who accessed the masked production data?" → No answer

```json
// ❌ WRONG: No audit logs
{
  "event": "data_provision",
  "dataset_id": "ds_abc123",
  "record_count": 10000
  // Missing: user_id, timestamp, operation, status
}

// ✅ CORRECT: Complete audit trail
{
  "timestamp": "2024-01-15T10:30:45Z",
  "event": "data_provision",
  "user_id": "engineer_john",
  "environment": "staging",
  "dataset_id": "ds_abc123",
  "operations": [
    {
      "action": "hash",
      "field": "email",
      "record_count": 10000,
      "status": "success"
    },
    {
      "action": "redact",
      "field": "phone",
      "record_count": 10000,
      "status": "success"
    }
  ],
  "validation": {
    "referential_integrity": "passed",
    "schema_validation": "passed"
  },
  "compliance_check": {
    "gdpr_compliant": true,
    "ccpa_compliant": true
  }
}
```

**Fix**:
- Log all data operations to immutable audit log
- Include user_id, timestamp, operation, status, result
- Encrypt audit logs at rest
- Retain audit logs per regulatory requirements (typically 1-7 years)

#### Pitfall 7: Slow Environment Provisioning

**Symptom**: 45+ minutes to provision test environment

**Root Causes**:
- ❌ Manual infrastructure setup
- ❌ Sequential database initialization
- ❌ Data generation without batching
- ❌ Lack of pre-built images/snapshots

```yaml
# ❌ WRONG: Sequential, manual process
1. Request environment (manual form)               # 5 min
2. Provision VM (Terraform)                        # 10 min
3. Install dependencies                            # 5 min
4. Create databases & tables                       # 5 min
5. Generate test data (serial)                     # 15 min
6. Run validation tests                            # 5 min
TOTAL: 45 minutes ❌

# ✅ CORRECT: Automated, parallelized
1. Trigger CI/CD (push code)
2. Pull pre-built Docker image                     # 10 sec
3. Start containers (parallel)                     # 20 sec
4. Provision data (batched)                        # 20 sec
5. Health checks (parallel)                        # 10 sec
TOTAL: < 2 minutes ✅
```

**Fix**:
- Use Docker for fast image reuse
- Pre-build images with base schema
- Batch data generation
- Run health checks in parallel
- Cache intermediate results

---

## Summary & Next Steps

### What You've Learned

This document provides a **production-grade test data management strategy** that you can apply to any project:

1. **Core Principles**: Determinism, isolation, compliance, automation
2. **Architecture**: Layered design (consumer, interface, provisioning, storage)
3. **Lifecycle**: Complete journey from specification to cleanup
4. **Environments**: Local, CI/CD, staging, and production-masked approaches
5. **Quality**: Schema validation, consistency patterns, referential integrity
6. **Security**: PII classification, masking strategies, audit logging
7. **Tools**: Factories, CLIs, APIs, Docker, Kubernetes
8. **Implementation**: Step-by-step checklist and timeline
9. **Best Practices**: What works, and what doesn't (with fixes)

### Implementation Path for Your Project

**Start Here** (if adopting this strategy):

```
Week 1-2:  Specify data schemas in YAML + classify PII
Week 3-4:  Build factories and Docker Compose for local dev
Week 5-6:  Integrate with CI/CD pipeline + REST API
Week 7-8:  Add compliance, monitoring, and documentation
```

### Reusability Across Projects

This strategy is **technology-agnostic** and adapts to:
- **Different databases**: MongoDB, PostgreSQL, MySQL, DynamoDB
- **Different domains**: E-commerce, SaaS, FinTech, HealthTech
- **Different scales**: 100 records to 1 billion+
- **Different compliance**: GDPR, CCPA, HIPAA, SOC2

Simply customize:
- Data factory classes (per domain)
- Schema definitions (per database)
- Masking policies (per regulation)
- Environment configs (per infrastructure)

**Core concepts remain constant** across all projects.

---

## Appendix: Quick Reference

### CLI Commands Cheat Sheet

```bash
# Provision data
data-cli provision --env local --dataset all
data-cli provision --env ci --dataset users --count 500

# Check health
data-cli health check
data-cli health check --execution-id abc123

# View data
data-cli show --collection users --limit 10
data-cli show --collection movies --filter '{"year": 2024}'

# Clean up
data-cli cleanup --execution-id abc123

# Export/Import
data-cli export --collection users --format json --output users.json
data-cli import --file users.json --collection users_backup
```

### Docker Compose Quick Start

```bash
# Start all services
docker-compose up -d

# Provision data
docker-compose exec data-provisioner data-cli provision --env local --dataset all

# View logs
docker-compose logs -f mongodb
docker-compose logs -f api

# Stop all
docker-compose down
```

### REST API Quick Start

```bash
# Provision
curl -X POST http://localhost:8000/api/v1/provision \
  -H "Content-Type: application/json" \
  -d '{"environment": "ci", "dataset": "all"}'

# Health check
curl http://localhost:8000/api/v1/health/abc123

# Cleanup
curl -X POST http://localhost:8000/api/v1/cleanup/abc123
```

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Author**: Engineering Team  
**Audience**: All engineering roles  
**License**: Internal Use Only

---

*This document serves as a reference template for implementing test data management across projects. Customize for your specific needs while maintaining core principles.*
