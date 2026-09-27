# Salary Management System

### Requirements & Product Scope

## 1. Goal

Build a web-based salary management system that replaces ACME's spreadsheet-driven salary workflow with a reliable, understandable, and scalable system for managing compensation data across a 10,000-employee organization.

The system should enable an HR Manager to efficiently manage employee salary information and answer meaningful questions about how compensation is distributed across the organization.

The objective is not to reproduce Excel in a browser, but to provide a structured source of truth that makes salary management and organizational compensation analysis easier, faster, and less error-prone.

## 2. Primary User

**HR Manager**

The HR Manager is responsible for maintaining employee salary information and using that information to understand compensation patterns across the organization.

The initial product is intentionally designed around this single persona rather than introducing multiple user roles without a demonstrated requirement.

## 3. Scope

### In Scope

#### Employee & Salary Management

* View a searchable list of employees.
* Search and filter employees using relevant attributes such as country, department, and job title.
* View an employee's salary information.
* Update an employee's salary through a controlled workflow.
* Validate salary-related inputs before persistence.

#### Compensation Insights

Provide useful organizational-level views that help answer questions such as:

* What is the organization's overall salary distribution?
* How does compensation vary across countries?
* How does compensation vary across departments or roles?
* What are the average, median, minimum, and maximum salaries within a selected population?

Where salary comparisons span countries with different currencies, the system will clearly distinguish monetary values rather than presenting incomparable amounts as though they share the same unit.

#### Data Initialization

* Provide a deterministic seed mechanism capable of generating 10,000 employees.
* Ensure seeded data is sufficiently realistic to exercise search, filtering, aggregation, and UI behavior.

## 4. Product Principles

### Correctness over cleverness

Salary data is business-critical information. The system should favor explicit validation, predictable behavior, and understandable code over unnecessary abstraction.

### Optimize for the HR workflow

The interface should answer common HR questions with minimal navigation rather than exposing database-oriented CRUD operations as the product experience.

### Make important behavior observable

Business rules and data transformations should be represented explicitly enough that they can be tested and reasoned about independently.

### Design for today's problem without prematurely solving tomorrow's

The architecture should comfortably support 10,000 employees while avoiding infrastructure and abstractions whose complexity is not justified by the current requirements.

## 5. Non-Goals / Deliberately Out of Scope

The following are intentionally excluded from the initial release unless clarified as required:

* Payroll processing or salary disbursement.
* Tax calculation and statutory compliance.
* Benefits administration.
* Employee self-service.
* Performance management.
* Recruitment or onboarding workflows.
* Complex role-based access-control hierarchies.
* Real-time collaboration.
* Notifications and workflow automation.
* Currency exchange-rate management.
* Distributed/microservice architecture.

These exclusions keep the assessment focused on salary management and compensation insight while leaving room for future evolution.

## 6. Key Assumptions

* The primary user is an authorized HR Manager.
* The system manages salary information rather than executing payroll.
* The organization contains employees across multiple countries.
* Salary data may involve multiple currencies; monetary values must therefore retain their currency context.
* 10,000 employees is the initial operating scale and should be handled comfortably without specialized distributed infrastructure.
* The application should be deployable and usable end-to-end, including backend, UI, database, seeded data, and tests.

Any assumption that materially affects the product or architecture will be validated where the assessment specification remains ambiguous.

## 7. Success Criteria

The solution is successful when an HR Manager can:

1. Locate an employee quickly.
2. Understand the employee's current salary information.
3. Safely update salary information.
4. Filter and explore salary data across meaningful organizational dimensions.
5. Obtain useful compensation statistics without manually processing spreadsheets.
6. Reliably work with the organization's 10,000-employee dataset.
7. Trust that core salary behavior is covered by fast, deterministic automated tests.

From an engineering perspective, the system should demonstrate clear design reasoning, maintainable code, meaningful tests, intentional AI usage, and an architecture proportionate to the problem.

## 8. Open Questions

The assessment leaves several product decisions unspecified. Before implementation, the following should be clarified where necessary:

1. **Salary representation:** Should salary be represented as annual compensation, monthly compensation, or another defined unit?
2. **Multi-currency analysis:** Should cross-country compensation analysis use local currencies only, or should the system normalize values into a common currency?
3. **Salary history:** Should salary changes maintain historical records, or is the current salary sufficient?
4. **Analytics scope:** What specific organizational compensation questions are expected beyond basic aggregation and comparison?
5. **Authentication:** Should authentication/authorization be implemented, or can the application assume an authorized HR Manager?
6. **Deployment:** Is there a preferred deployment environment, or is any publicly accessible deployment acceptable?

These questions are intentionally separated from assumptions so that unresolved product decisions are not silently encoded into the implementation.

## 9. Engineering Scope

The implementation will be delivered as a complete, deployable application consisting of:

* Python backend
* Relational database
* React/Next.js user interface
* Deterministic 10,000-employee seed capability
* Automated tests covering core business behavior
* Deployment configuration
* Architecture and design documentation
* AI workflow and relevant prompts
* Documented trade-offs and performance considerations
* Incremental Git commits demonstrating the evolution of the solution

