# Architecture & Design

## 1. Architecture Overview

The application will use a modular monolith architecture with a React/Next.js frontend, Python backend, and relational database.

The design is organized around business capabilities rather than technical CRUD operations:

- Employee Management
- Compensation Management
- Compensation Insights

The system is intentionally simple enough to develop, test, and deploy as a single application while keeping domain boundaries explicit for future evolution.

---

## 2. Architectural Decisions

### Decision 1 — Modular Monolith over Microservices

**Decision:** Use a modular monolith.

**Why:** The initial scale is 10,000 employees and the domain is relatively bounded. Distributed services would introduce operational, deployment, and debugging complexity without a demonstrated need.

**Trade-off:** We give up independent service deployment and scaling, but gain simplicity and lower operational overhead.

---

### Decision 2 — Relational Database

**Decision:** Use a relational database.

**Why:** Employee and compensation data is structured and relational, requires transactional updates, and supports aggregation-heavy queries.

**Trade-off:** A relational model requires deliberate schema design, but provides strong consistency, constraints, and efficient analytical queries for the expected scale.

---

### Decision 3 — Separate Employee and Compensation Domains

**Decision:** Model employee identity separately from compensation.

**Why:** An employee's identity and organizational attributes have a different lifecycle from compensation.

**Benefit:** Compensation can evolve independently without coupling salary behavior to the employee entity.

---

### Decision 4 — Database-Side Aggregation

**Decision:** Perform compensation aggregations in the database.

**Why:** Aggregations such as averages, counts, minimums, and maximums are data-intensive operations. Executing them close to the data avoids unnecessarily transferring large datasets into application memory.

**Trade-off:** Analytics logic becomes more dependent on database queries, but this is appropriate for the relational and aggregation-oriented workload.

---

### Decision 5 — Paginated Employee Queries

**Decision:** Paginate employee-list responses.

**Why:** The system manages 10,000 employees. Returning the complete dataset for every request would create unnecessary network, memory, and rendering overhead.

**Decision:** The API will enforce a bounded page size.

---

### Decision 6 — Explicit Domain Capabilities over Generic CRUD Abstractions

**Decision:** Organize application behavior around business capabilities rather than generic CRUD abstractions.

**Why:** The product exists to support HR workflows, not to expose database operations.

Examples:

- Find employees
- View compensation
- Update compensation
- Analyze compensation

This keeps business intent visible in the code and avoids premature generic abstractions.

---

## 3. Application Boundaries

```text
Frontend
   ↓
API / Request Validation
   ↓
Application Services
   ↓
Domain Rules
   ↓
Repositories
   ↓
Relational Database