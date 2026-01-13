# 6. OPERATING MODEL: SELF-SERVICE & AUTOMATION GOVERNANCE

## 6.1 Self-Service Automation Model

### 6.1.1 Developer Self-Service Portal

```
┌─────────────────────────────────────────────────────────────────┐
│           ISTA SELF-SERVICE PORTAL                              │
│        (Web Dashboard + CLI + REST API)                         │
└─────────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
        ┌─────────┐   ┌──────────┐   ┌──────────────┐
        │ Test    │   │Environment│   │Data         │
        │ Suites  │   │Creation   │   │Provisioning │
        └─────────┘   └──────────┘   └──────────────┘
            │               │               │
            ├─ View Results  ├─ Monitor      ├─ Track Status
            ├─ Re-run Test   ├─ Logs         ├─ Refresh Data
            └─ Share Logs    └─ Cleanup      └─ View Schema
```

### 6.1.2 Self-Service Web Dashboard

```python
# Operating Model example: Dashboard API endpoints

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
import os

app = FastAPI(title="ISTA Self-Service Portal")

# Authentication
def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))) -> str:
    """Extract user from token"""
    return decode_token(token)["sub"]

# Models
class ProvisionDataRequest(BaseModel):
    datasets: List[str]
    volumes: Dict[str, int]
    apply_masking: bool = True
    retention_hours: int = 2
    notify_email: str = None

class CreateTestEnvRequest(BaseModel):
    name: str
    services: List[str]
    retention_hours: int = 2
    notify_email: str = None

class ExecuteTestRequest(BaseModel):
    test_suite: str
    environment_id: str
    notify_on_completion: bool = True

# Endpoints: Data Provisioning
@app.post("/api/v1/data/provision")
async def provision_data(
    request: ProvisionDataRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Self-service endpoint for test data provisioning.
    
    Example:
    POST /api/v1/data/provision
    {
        "datasets": ["users", "orders"],
        "volumes": {"users": 100, "orders": 500},
        "apply_masking": true,
        "retention_hours": 2,
        "notify_email": "alice@company.com"
    }
    """
    # Check permissions
    rbac = RBACEnforcer()
    if not rbac.check_permission(current_user, Permission.DATA_CREATE):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Enforce governance policy
    policy_enforcer = OPAPolicyEnforcer()
    try:
        policy_enforcer.enforce_data_provisioning({
            "apply_masking": request.apply_masking,
            "volumes": request.volumes,
            "retention_days": request.retention_hours / 24,
            "user_roles": ["developer"]  # From IdP
        })
    except PermissionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Provision data
    from test_data_automation.data_provision_api import DataProvisioningService
    
    service = DataProvisioningService()
    result = service.provision({
        "datasets": request.datasets,
        "volumes": request.volumes,
        "apply_masking": request.apply_masking
    })
    
    # Log audit event
    audit_logger.log_data_provisioning(
        actor=current_user,
        datasets=request.datasets,
        volumes=request.volumes,
        masking_applied=request.apply_masking
    )
    
    # Send notification
    if request.notify_email:
        send_email(
            to=request.notify_email,
            subject="Test Data Provisioned",
            body=f"Data provisioned: {result['record_counts']}"
        )
    
    return {
        "status": "success",
        "request_id": result["request_id"],
        "record_counts": result["record_counts"],
        "expires_at": result["expires_at"]
    }

@app.get("/api/v1/data/status/{request_id}")
async def get_data_provision_status(
    request_id: str,
    current_user: str = Depends(get_current_user)
):
    """Check status of data provisioning"""
    # Implementation...
    pass

# Endpoints: Environment Management
@app.post("/api/v1/environments/create")
async def create_test_environment(
    request: CreateTestEnvRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Self-service test environment creation.
    
    Example:
    POST /api/v1/environments/create
    {
        "name": "my-e2e-test",
        "services": ["postgres", "redis", "api"],
        "retention_hours": 2,
        "notify_email": "alice@company.com"
    }
    """
    # Check permissions
    rbac = RBACEnforcer()
    if not rbac.check_permission(current_user, Permission.ENV_CREATE):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Check governance
    policy_enforcer = OPAPolicyEnforcer()
    try:
        policy_enforcer.enforce_environment_creation({
            "user_roles": ["developer"],
            "environment": "test",
            "rbac_enforced": True
        })
    except PermissionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create environment
    env_manager = EnvironmentManager()
    env_details = env_manager.create(
        name=request.name,
        services=request.services,
        ttl_hours=request.retention_hours,
        owner=current_user
    )
    
    # Audit log
    audit_logger.log_environment_creation(
        actor=current_user,
        environment_id=env_details["id"],
        environment_details=env_details
    )
    
    return {
        "id": env_details["id"],
        "name": env_details["name"],
        "status": "provisioning",
        "endpoints": env_details["endpoints"],
        "expires_at": env_details["expires_at"]
    }

@app.get("/api/v1/environments/{environment_id}")
async def get_environment(
    environment_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get environment details and status"""
    # Implementation...
    pass

@app.delete("/api/v1/environments/{environment_id}")
async def delete_environment(
    environment_id: str,
    current_user: str = Depends(get_current_user)
):
    """Self-service environment cleanup"""
    # Implementation...
    pass

# Endpoints: Test Execution
@app.post("/api/v1/tests/execute")
async def execute_test(
    request: ExecuteTestRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Self-service test execution.
    
    Example:
    POST /api/v1/tests/execute
    {
        "test_suite": "e2e-checkout",
        "environment_id": "env-12345",
        "notify_on_completion": true
    }
    """
    # Check permissions
    rbac = RBACEnforcer()
    if not rbac.check_permission(current_user, Permission.PIPELINE_EXECUTE):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Execute test
    test_runner = TestRunner()
    execution = test_runner.run(
        suite=request.test_suite,
        environment_id=request.environment_id,
        executor=current_user
    )
    
    # Audit log
    audit_logger.log_event(
        event_type=AuditEventType.PIPELINE_EXECUTED,
        actor=current_user,
        action="EXECUTE",
        resource_type="test_suite",
        resource_id=execution["id"],
        resource_details={"suite": request.test_suite},
        result="success"
    )
    
    return {
        "execution_id": execution["id"],
        "status": "running",
        "logs_url": f"/api/v1/executions/{execution['id']}/logs"
    }

@app.get("/api/v1/test-suites")
async def list_test_suites(
    current_user: str = Depends(get_current_user)
):
    """List available test suites for user"""
    return {
        "suites": [
            {
                "name": "e2e-checkout",
                "description": "End-to-end checkout flow",
                "estimated_duration": "5 minutes",
                "required_environment": ["postgres", "redis", "api"]
            },
            {
                "name": "e2e-account",
                "description": "Account management tests",
                "estimated_duration": "3 minutes",
                "required_environment": ["postgres", "api"]
            },
            {
                "name": "integration-api",
                "description": "API integration tests",
                "estimated_duration": "4 minutes",
                "required_environment": ["postgres", "redis"]
            }
        ]
    }

# Health & Status
@app.get("/api/v1/health")
async def health_check():
    """Portal health check"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

## 6.2 Dev/QA/Ops Ownership Boundaries

### 6.2.1 RACI Matrix (Responsible, Accountable, Consulted, Informed)

```
┌────────────────────────────────────────────────────────────────────────┐
│                          RESPONSIBILITY MATRIX                         │
├────────────────────────────┬────────┬─────────┬──────┬─────────────────┤
│ ACTIVITY                   │ DEV    │ QA AUTO │ OPS  │ SECURITY        │
├────────────────────────────┼────────┼─────────┼──────┼─────────────────┤
│ Test Case Design           │ R/A    │ C       │      │ C               │
│ Test Data Definition       │ C      │ R/A     │      │ C               │
│ Data Provisioning API      │        │ R/A     │ C    │ C               │
│ Environment Templating     │        │ C       │ R/A  │ C               │
│ Infrastructure Provisioning│        │ C       │ R/A  │ C               │
│ CI/CD Pipeline Config      │        │ R/A     │ C    │ C               │
│ RBAC Policy Definition     │        │         │      │ R/A             │
│ PII Masking Rules          │        │ C       │      │ R/A             │
│ Audit Logging              │        │ C       │ C    │ R/A             │
│ Secret Management          │        │         │ R/A  │ C               │
│ Compliance Reporting       │        │         │      │ R/A             │
│ Framework Maintenance      │ I      │ R/A     │ C    │ C               │
│ Runbook Documentation      │ C      │ R/A     │ C    │ C               │
│ Support & Escalation       │ C      │ R/A     │ C    │ C               │
└────────────────────────────┴────────┴─────────┴──────┴─────────────────┘

R = Responsible (Does the work)
A = Accountable (Final decision maker)
C = Consulted (Provides input)
I = Informed (Kept in the loop)
```

### 6.2.2 Team Responsibilities

#### **Developers**
- ✅ Write test cases using framework
- ✅ Define test data requirements
- ✅ Run tests locally (shift-left)
- ✅ Consume provisioning APIs
- ✅ Report issues/bugs
- ❌ Manage infrastructure
- ❌ Define RBAC policies
- ❌ Approve compliance policies

#### **QA Automation Engineers**
- ✅ Build test automation framework
- ✅ Design test data schemas
- ✅ Implement data provisioning APIs
- ✅ Create CI/CD pipeline templates
- ✅ Manage test suites
- ✅ Execute tests & analyze results
- ✅ Own framework documentation
- ❌ Manage cloud infrastructure
- ❌ Define security policies

#### **DevOps / Platform Engineers**
- ✅ Provision cloud infrastructure
- ✅ Deploy and scale Kubernetes clusters
- ✅ Manage infrastructure secrets
- ✅ Implement cost controls
- ✅ Monitor infrastructure health
- ✅ Provide infrastructure templates
- ❌ Design test data schemas
- ❌ Define RBAC policies
- ❌ Approve compliance policies

#### **Security / Compliance**
- ✅ Define RBAC and access control policies
- ✅ Approve PII masking rules
- ✅ Audit logging implementation
- ✅ Compliance policy definition (OPA)
- ✅ Secret rotation strategies
- ✅ Audit log review & compliance reporting
- ❌ Build test automation
- ❌ Provision infrastructure

---

## 6.3 Automation Onboarding Process

### 6.3.1 Developer Onboarding (Week 1-2)

```
Day 1-2: Framework Introduction
├─ 30-min: Framework overview & architecture
├─ 30-min: Tour of self-service portal
├─ 1 hour: Setting up local development
│  └─ git clone ista-framework
│  └─ docker-compose up (test environment)
│  └─ ista-data provision --scenario=basic
└─ 30-min: Running first test locally

Day 3-4: Writing Test Cases
├─ 2 hours: Test case patterns & examples
├─ 2 hours: Hands-on: Write 3 test cases
├─ 1 hour: Using @requires_test_data decorator
├─ 30-min: Understanding data isolation
└─ Homework: Write 5 integration tests

Day 5: CI/CD Integration
├─ 1 hour: Understanding pipeline stages
├─ 30-min: How tests run in CI
├─ 30-min: Reading test reports
├─ 1 hour: Debugging failed tests
└─ 30-min: Best practices & review

Deliverables:
✅ Local test environment running
✅ 5 integration tests written
✅ First test passing in CI pipeline
✅ Able to read & understand test reports
```

### 6.3.2 QA Automation Engineer Onboarding (Week 1-4)

```
Week 1: Framework Architecture
├─ Day 1-2: Deep dive into framework components
│  └─ Data generation, masking, provisioning
│  └─ Environment automation (Terraform, Docker)
│  └─ CI/CD orchestration
├─ Day 3-4: Understanding codebase
│  └─ GitHub tour, architecture diagrams
│  └─ Key files & patterns
└─ Day 5: Framework labs
   └─ Hands-on with each component

Week 2: Test Data Automation
├─ Build data schemas for sample microservice
├─ Implement data factory patterns
├─ Create data provisioning API endpoints
├─ Deploy data provisioning service
└─ Validation & testing

Week 3: Environment Automation
├─ Write Terraform for ephemeral environments
├─ Create Docker Compose for local dev
├─ Implement health checks
├─ Create provisioning/teardown scripts
└─ Test full end-to-end flow

Week 4: CI/CD & Framework Mastery
├─ Create GitHub Actions workflow
├─ Implement parallel test execution
├─ Create aggregation & reporting
├─ Framework documentation updates
└─ Framework support rotation begins

Deliverables:
✅ Comfortable modifying all framework components
✅ Can add new test data types independently
✅ Can troubleshoot automation issues
✅ Ready to support other teams
✅ Framework knowledge documented
```

### 6.3.3 DevOps Engineer Onboarding (Week 1-2)

```
Day 1-2: Infrastructure Overview
├─ Overview of test infrastructure
├─ Terraform templates review
├─ Kubernetes manifests walkthrough
└─ Cost tracking & optimization

Day 3-4: Hands-on Infrastructure
├─ Deploy test environments using Terraform
├─ Set up cost monitoring
├─ Configure auto-scaling policies
├─ Troubleshoot infrastructure issues
└─ Understand secrets management

Day 5: Support & Operations
├─ Onboarding complete check-in
├─ Documentation review
├─ Support model explanation
└─ Questions & clarifications

Deliverables:
✅ Can provision/destroy test environments
✅ Can troubleshoot infrastructure issues
✅ Comfortable with secrets management
✅ Understands cost implications
```

---

## 6.4 Support & Escalation Model

### 6.4.1 Support Channels & SLA

```
┌─────────────────────────────────────────────────────────────────┐
│           ISTA SUPPORT MODEL (3-TIER)                          │
└─────────────────────────────────────────────────────────────────┘

TIER 1: Self-Service & Documentation
├─ Slack channel: #ista-support
├─ Wiki: https://wiki.company.com/ista
├─ GitHub Issues: ista-framework/issues
├─ Response time: Async (best effort)
└─ Owner: Community (all engineers)

TIER 2: QA Automation Team (Business Hours)
├─ Slack channel: @ista-team
├─ Response time SLA: 4 hours
├─ Issues: Data provisioning, test execution
├─ Escalation: When self-service insufficient
└─ Owner: QA Automation Engineers

TIER 3: Platform/DevOps (Critical)
├─ Slack channel: @oncall-platform
├─ Response time SLA: 1 hour
├─ Issues: Infrastructure down, data loss, security
├─ Escalation: When tests blocked enterprise-wide
└─ Owner: DevOps Engineers

OUTSIDE HOURS:
├─ Critical issues: PagerDuty oncall
├─ Non-critical: Queued for morning standup
└─ 24/7 monitoring: Infrastructure health only
```

### 6.4.2 Common Issues & Resolution Paths

```python
# Support runbook automation

ISSUES_RESOLUTION_MAP = {
    
    "Data provisioning timeout": {
        "symptoms": ["Provision API returns 504", "Data loads >5 minutes"],
        "investigation": [
            "Check database connectivity",
            "Verify data volumes",
            "Check masking rules performance"
        ],
        "resolution": [
            "Reduce data volumes",
            "Optimize masking queries",
            "Scale database instance"
        ],
        "owner": "QA Automation",
        "slack_thread": "#ista-support",
        "runbook": "docs/troubleshooting/data-provisioning-slow.md"
    },
    
    "Tests failing with 'connection refused'": {
        "symptoms": ["PostgreSQL connection errors", "Redis timeout"],
        "investigation": [
            "Check environment health checks",
            "Verify service startup order",
            "Check network configuration"
        ],
        "resolution": [
            "Re-run health checks",
            "Increase service startup timeout",
            "Check Docker/K8s logs"
        ],
        "owner": "DevOps",
        "slack_thread": "#ista-support",
        "runbook": "docs/troubleshooting/connectivity-issues.md"
    },
    
    "Test data isolation failures": {
        "symptoms": ["Tests interfering with each other", "Duplicate key errors"],
        "investigation": [
            "Verify each test gets unique data",
            "Check data cleanup between runs",
            "Verify data contract definitions"
        ],
        "resolution": [
            "Add @requires_test_data decorator",
            "Update data factory patterns",
            "Increase data volume for uniqueness"
        ],
        "owner": "QA Automation",
        "slack_thread": "#ista-support",
        "runbook": "docs/troubleshooting/data-isolation.md"
    },
    
    "Compliance policy violations": {
        "symptoms": ["Pipeline fails with 'Policy violation'", "Masking not applied"],
        "investigation": [
            "Check OPA policy logs",
            "Verify RBAC configuration",
            "Check masking rule definitions"
        ],
        "resolution": [
            "Review policy in OPA",
            "Fix request parameters",
            "Escalate to Security if policy too strict"
        ],
        "owner": "Security / QA Automation",
        "slack_thread": "#ista-support",
        "runbook": "docs/troubleshooting/policy-violations.md"
    },
}

class AutomatedSupportTriage:
    """Automatically route issues and suggest solutions"""
    
    def triage_issue(self, error_message: str, logs: str) -> Dict[str, Any]:
        """
        Analyze error and suggest resolution.
        """
        # ML-based classification
        issue_type = self.classify_error(error_message, logs)
        
        # Get resolution path
        resolution = ISSUES_RESOLUTION_MAP.get(issue_type, {})
        
        return {
            "issue_type": issue_type,
            "owner": resolution.get("owner"),
            "suggested_steps": resolution.get("resolution"),
            "runbook": resolution.get("runbook"),
            "slack_channel": resolution.get("slack_thread"),
            "escalation_needed": self._needs_escalation(issue_type)
        }
    
    def _needs_escalation(self, issue_type: str) -> bool:
        """Determine if issue needs escalation"""
        critical_issues = [
            "Compliance policy violations",
            "Infrastructure down",
            "Data corruption detected"
        ]
        return issue_type in critical_issues
```

---

## 6.5 KPIs & Success Metrics

### 6.5.1 Framework Adoption Metrics

| Metric | Current | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|---------|----------|
| **Dev Team Adoption** | 5% | 35% | 70% | 90% |
| **Test Automation Coverage** | 20% | 50% | 80% | 100% |
| **Shift-Left Test Runs (local)** | 0% | 15% | 40% | 60% |
| **Manual Env Creation** | 100% | 50% | 10% | 0% |
| **Self-Service Usage** | 0% | 20% | 70% | 85% |
| **Framework Support Tickets** | 0 | 15/week | 25/week | 20/week |

### 6.5.2 Operational Metrics

| Metric | Target | Owner |
|--------|--------|-------|
| **Environment Setup Time** | <2 min | DevOps |
| **Test Execution Time** | <10 min (50 parallel jobs) | QA Auto |
| **Data Provisioning** | <30 sec | QA Auto |
| **Mean Time to Recovery (env issues)** | <10 min | DevOps |
| **Framework Support SLA** | 4 hours | QA Auto |
| **Test Flakiness (env-caused)** | <2% | QA Auto |

---

## 6.6 Continuous Improvement Process

### 6.6.1 Monthly Review Cadence

```
MONTHLY FRAMEWORK REVIEW (1st Friday, 10am)

Agenda:
├─ Review KPIs (30 min)
│  ├─ Adoption rate
│  ├─ Performance metrics
│  ├─ Issue/ticket trends
│  └─ Cost metrics
│
├─ Address top issues (30 min)
│  ├─ Most common failures
│  ├─ Performance bottlenecks
│  └─ Usability friction
│
├─ Proposed enhancements (30 min)
│  ├─ Feature requests from teams
│  ├─ Framework improvements
│  └─ Tooling additions
│
└─ Roadmap updates (30 min)
   ├─ Next month priorities
   ├─ Resource allocation
   └─ Timeline adjustments

Attendees:
├─ QA Automation leads
├─ DevOps representative
├─ Security representative
├─ Product teams (rotating)
└─ Framework maintainers

Output:
├─ Updated KPI dashboard
├─ Prioritized issues list
├─ Proposed roadmap updates
└─ Distribution to stakeholders
```

---

## Summary: Operating Model

**Self-Service Enablement**:
- ✅ Web portal + REST API + CLI for provisioning
- ✅ Zero-training test execution
- ✅ Intuitive data provisioning interface

**Clear Ownership**:
- ✅ RACI matrix defines responsibilities
- ✅ Separated concerns (Dev/QA/Ops/Security)
- ✅ Escalation paths defined

**Successful Onboarding**:
- ✅ Structured 2-4 week programs
- ✅ Hands-on labs & deliverables
- ✅ Graduated responsibility

**Responsive Support**:
- ✅ 3-tier support model with SLAs
- ✅ Automated issue triage
- ✅ Comprehensive runbooks

**Continuous Improvement**:
- ✅ Monthly reviews with metrics
- ✅ Community feedback loops
- ✅ Data-driven roadmap planning

---

## 6.7 Document Summary & Quick Reference

| Document | Purpose | Key Content |
|----------|---------|------------|
| **README.md** | Framework overview | Vision, benefits, structure |
| **01_AUTOMATION_STRATEGY.md** | Strategic vision | Problems, goals, architecture |
| **02_TEST_DATA_AUTOMATION.md** | Data automation | Generators, masking, APIs |
| **03_TEST_ENVIRONMENT_AUTOMATION.md** | Environment automation | IaC, containers, health checks |
| **04_CI_CD_INTEGRATION.md** | Pipeline orchestration | GitHub Actions, orchestration, resilience |
| **05_GOVERNANCE_AUTOMATION.md** | Compliance & governance | RBAC, audit logging, policies |
| **06_OPERATING_MODEL.md** | Operational excellence | Self-service, support, metrics |

---

## Final Checklist: Implementation Readiness

### Pre-Launch (Week -4 to -1)
- [ ] Approve automation strategy
- [ ] Allocate resources (2-3 platform engineers)
- [ ] Set up GitHub repos (ista-framework, ista-data, ista-infra)
- [ ] Configure CI/CD platform
- [ ] Establish security policies

### Phase 1: Shift-Left (Weeks 1-4)
- [ ] Local dev environment (Docker Compose)
- [ ] Data provisioning CLI tool
- [ ] Test data examples & documentation
- [ ] Developer training sessions
- [ ] Internal team rollout

### Phase 2: CI/CD Automation (Weeks 5-8)
- [ ] GitHub Actions workflows
- [ ] Parallel test orchestration
- [ ] Infrastructure provisioning (Terraform)
- [ ] Test execution pipelines
- [ ] Reporting & aggregation

### Phase 3: Governance (Weeks 9-12)
- [ ] RBAC policies & enforcement
- [ ] PII masking rules (DB + app)
- [ ] Audit logging system
- [ ] Policy-as-Code (OPA)
- [ ] Compliance reporting

### Phase 4: Enterprise Scale (Weeks 13-16)
- [ ] Self-service portal
- [ ] Secret management
- [ ] Multi-tenant support
- [ ] Cost optimization
- [ ] Enterprise onboarding

---

## Contact & Support

**Framework Maintainers**: qa-automation@company.com  
**Slack Channel**: #ista-framework  
**GitHub Repo**: github.com/company/ista-framework  
**Wiki**: https://wiki.company.com/ista  
**Issues**: github.com/company/ista-framework/issues  

---

**Document Status**: Ready for Implementation  
**Target Completion**: 16 weeks to full enterprise adoption  
**Investment**: 2-3 FTE engineers  
**Expected ROI**: 3-5x cost savings + 4x speed improvement
