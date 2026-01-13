# ISTA Implementation Quick Start Guide

## 📋 Prerequisites

### Required Software
- Python 3.11+
- Docker & Docker Compose
- Terraform 1.6+
- Git
- AWS CLI or similar cloud CLI
- kubectl (for Kubernetes)

### Infrastructure Requirements
- AWS Account (or equivalent cloud provider)
- GitHub/GitLab with Actions/CI enabled
- Kubernetes cluster (EKS, AKS, or local with Kind)
- PostgreSQL database
- Redis cluster

---

## 🚀 Quick Start (15 minutes)

### For MongoDB Users (New!)
If you're using MongoDB Atlas with the `sample_mflix` database, follow the **[MongoDB Quick Start Guide](MONGODB_QUICK_START.md)** instead. That guide covers:
- Provisioning test data from your MongoDB collections
- Using the MongoDB CLI tool
- Writing tests with data factories
- Database adapter patterns

---

### For PostgreSQL Users (Original)

#### Step 1: Clone Repository
```bash
git clone https://github.com/company/ista-framework.git
cd ista-framework
```

### Step 2: Local Development Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start local environment
docker-compose -f test-environment-automation/docker/docker-compose.yml up -d

# Verify services are healthy
sleep 10  # Wait for services to start
docker-compose -f test-environment-automation/docker/docker-compose.yml ps

# Expected output:
# - postgres  UP
# - redis     UP
# - api       UP (health check passing)
```

### Step 3: Provision Test Data
```bash
# Start data provisioning API
python -m test_data_automation.data_provision_api &

# Provision data in another terminal
python test-data-automation/ista_data_cli.py provision \
  --datasets users,orders \
  --volumes '{"users":100,"orders":500}'

# Expected: Data provisioned successfully in <30 seconds
```

### Step 4: Run Your First Test
```bash
# Write a simple test
cat > test_example.py <<EOF
from test_data_automation.decorators import requires_test_data

@requires_test_data(
    datasets=["users", "orders"],
    volume={"users": 10, "orders": 50}
)
def test_checkout_flow(test_data):
    """Simple test using provisioned data"""
    users = test_data["users"]
    assert len(users) == 10
    print(f"✓ Test passed with {len(users)} users")

if __name__ == "__main__":
    test_checkout_flow()
EOF

# Run the test
python test_example.py

# Expected: Test passes, data is provisioned and cleaned up automatically
```

---

## 📊 Architecture Overview

```
┌─────────────────┐
│   Developers    │
└────────┬────────┘
         │
    ┌────┴────────────────────┐
    │                         │
    ▼                         ▼
┌──────────┐         ┌─────────────────┐
│ Local    │         │  CI/CD Platform │
│ Testing  │         │  (GitHub/GitLab)│
│ (2 min)  │         └────────┬────────┘
└────┬─────┘                  │
     │              ┌─────────┴──────────┐
     │              ▼                    ▼
     │        ┌──────────────┐    ┌────────────┐
     │        │ PROVISION    │    │ VALIDATE   │
     │        │ • Data       │    │ • Health   │
     │        │ • Environment│    │ • Schema   │
     │        └──────────────┘    └────────────┘
     │              │                    │
     └──────────────┼────────────────────┘
                    │
                    ▼
         ┌────────────────────┐
         │   TEST EXECUTION   │
         │  (Parallel 50 jobs)│
         └────────────────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
    ┌─────────┐           ┌─────────┐
    │ REPORT  │           │ CLEANUP │
    └─────────┘           └─────────┘
```

---

## 🛠️ Implementation Phases

### Phase 0: Local Development (Days 1-3)
**Goal**: Get local dev environment working

```bash
# Files to modify
test-environment-automation/docker/docker-compose.yml
test-data-automation/data_definitions/users.yaml

# Deliverable: Local tests running in <2 min
pytest tests/integration/ -v  # All tests pass
```

### Phase 1: Test Data Automation (Days 4-7)
**Goal**: Implement data provisioning

**Key Files**:
```
test-data-automation/
├── data_generator.py
├── data_masking.py
├── data_factories.py
├── data_provision_api.py
└── data_definitions/
    ├── users.yaml
    ├── orders.yaml
    └── payments.yaml
```

**Verify**:
```bash
# API running and responsive
curl http://localhost:8000/health

# Data provisioning works
python ista_data_cli.py provision --datasets users --volumes '{"users":100}'

# Masking applied correctly
psql -h localhost -U testadmin -d testdb -c "SELECT email FROM users LIMIT 1"
# Should show: masked-xxxxx@example.com
```

### Phase 2: Environment Automation (Days 8-11)
**Goal**: Implement Terraform + Docker environments

**Key Files**:
```
test-environment-automation/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   └── health_checks.py
└── provision_environment.sh
```

**Verify**:
```bash
# Terraform validates
cd test-environment-automation/terraform
terraform validate

# Environment provisions in <2 min
bash ../provision_environment.sh "test-$(date +%s)"

# Health checks pass
python ../health_checks.py
```

### Phase 3: CI/CD Integration (Days 12-15)
**Goal**: Deploy pipelines

**Key Files**:
```
ci-cd-pipelines/
├── github-actions/
│   └── .github/workflows/
│       ├── test-automation.yml
│       └── nightly-regression.yml
├── orchestration.py
├── resilience.py
└── report_generator.py
```

**Verify**:
```bash
# Push to GitHub
git push origin main

# Pipeline runs automatically
# Check GitHub Actions tab for results
```

### Phase 4: Governance (Days 16-19)
**Goal**: Add RBAC, masking, audit logging

**Key Files**:
```
governance/
├── rbac_enforcement.py
├── audit_logger.py
├── pii_masking_rules.sql
├── opa_policy_enforcer.py
└── secret_management.py
```

**Verify**:
```bash
# Audit logs being created
select count(*) from audit_log;

# RBAC enforced
python -c "from governance.rbac_enforcement import RBACEnforcer; ..."

# Policies enforced
pytest governance/tests/test_policies.py -v
```

### Phase 5: Self-Service Portal (Days 20-23)
**Goal**: Deploy web dashboard

**Verify**:
```bash
# Portal running
curl http://localhost:8080/health

# Can provision data via UI
# Can create environments via UI
# Can execute tests via UI
```

---

## 📝 Common Tasks

### Add a New Dataset

1. Create data specification:
```bash
cat > test-data-automation/data_definitions/new_dataset.yaml <<EOF
apiVersion: data.automation/v1
kind: DataDefinition
metadata:
  name: new_dataset
  version: v1.0.0

spec:
  source: synthetic
  table: public.new_dataset
  volume:
    count: 1000
  
  fields:
    - name: id
      type: integer
      generator: sequence
      start: 1
    
    - name: name
      type: varchar(255)
      generator: name
    
    - name: email
      type: varchar(255)
      generator: email
      masking: true
EOF
```

2. Update database schema:
```sql
CREATE TABLE public.new_dataset (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

3. Test provisioning:
```bash
ista-data provision --datasets new_dataset --volumes '{"new_dataset":100}'
```

### Add a New Test Suite

1. Create test file:
```bash
mkdir -p tests/e2e/my_feature
cat > tests/e2e/my_feature/test_my_feature.py <<EOF
from test_data_automation.decorators import requires_test_data

@requires_test_data(
    datasets=["users"],
    volume={"users": 10}
)
def test_my_feature(test_data):
    """My test case"""
    assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

2. Add to CI/CD:
```yaml
# .github/workflows/test-automation.yml
strategy:
  matrix:
    test-suite:
      - name: my-feature
        path: tests/e2e/my_feature
```

3. Run locally:
```bash
pytest tests/e2e/my_feature -v
```

---

## 🔍 Troubleshooting

### Data Provisioning Timeout
```bash
# Check database connectivity
psql -h localhost -U testadmin -d testdb -c "SELECT version()"

# Reduce data volumes
ista-data provision --datasets users --volumes '{"users":10}'

# Check API logs
tail -f ista_data_api.log
```

### Tests Failing with Connection Refused
```bash
# Check services are running
docker-compose -f test-environment-automation/docker/docker-compose.yml ps

# Restart services
docker-compose down && docker-compose up -d

# Run health checks
python test-environment-automation/health_checks.py
```

### Terraform Apply Fails
```bash
# Validate configuration
cd test-environment-automation/terraform
terraform validate

# Check AWS credentials
aws sts get-caller-identity

# Plan before apply
terraform plan -var pipeline_id=test-123
```

---

## 📚 Documentation Map

| Document | Purpose | Read Time |
|----------|---------|-----------|
| README.md | Framework overview | 10 min |
| 01_AUTOMATION_STRATEGY.md | Strategic context | 20 min |
| 02_TEST_DATA_AUTOMATION.md | Data framework | 30 min |
| 03_TEST_ENVIRONMENT_AUTOMATION.md | Environment framework | 30 min |
| 04_CI_CD_INTEGRATION.md | Pipeline orchestration | 30 min |
| 05_GOVERNANCE_AUTOMATION.md | Compliance & security | 20 min |
| 06_OPERATING_MODEL.md | Operations & support | 20 min |

---

## 🚨 Critical Success Factors

1. **Start Small**: Begin with single microservice, expand gradually
2. **Measure Everything**: Track KPIs from day 1
3. **Communicate Changes**: Weekly updates to teams
4. **Celebrate Wins**: Share success stories
5. **Listen to Feedback**: Iterate based on user feedback

---

## 📞 Getting Help

**Slack**: #ista-framework  
**Email**: sreelesh.kunnath@dinexora.de  
**Issues**: github.com/company/ista-framework/issues  
**Wiki**: https://wiki.company.com/ista  

---

## ✅ Implementation Checklist

- [ ] Clone repository
- [ ] Set up local environment
- [ ] Run first test locally
- [ ] Implement test data schemas
- [ ] Set up Terraform infrastructure
- [ ] Deploy CI/CD pipelines
- [ ] Implement governance policies
- [ ] Launch self-service portal
- [ ] Train first team
- [ ] Monitor KPIs
- [ ] Celebrate success!

---

**Status**: Ready for Implementation  
**Duration**: 4 weeks (1 FTE) to 3 weeks (3 FTE)  
**Expected Time to Production**: 4 weeks
