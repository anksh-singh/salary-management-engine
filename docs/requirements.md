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


## Compensation Model

The system models **annual gross base salary for full-time employees**.

Salary is stored together with its currency. The initial release retains each employee's local currency and does not perform currency conversion.

This avoids introducing exchange-rate management and prevents cross-currency comparisons from presenting misleading monetary values.

## Salary Lifecycle

The initial release manages the employee's **current salary only**.

Salary history and effective-dated compensation changes are intentionally excluded because they are not required for the core HR workflow and would introduce additional temporal business rules.

The data model remains structured so historical compensation can be introduced later without redesigning the employee domain.


#### Compensation Insights

The initial release will provide a focused set of HR-oriented insights:

- Employee count
- Salary distribution within a currency
- Average salary within a currency
- Median salary within a currency
- Minimum and maximum salary within a currency
- Breakdown by country
- Breakdown by department
- Breakdown by job title

Monetary statistics will be calculated within a currency context. The system will not aggregate amounts across currencies.

The insight set is intentionally focused on common compensation-management questions rather than attempting to build a general-purpose reporting platform.


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

## Deliberately Out of Scope

- Authentication and authorization
- Salary history
- Currency conversion / FX management
- Payroll processing
- Tax calculation
- Benefits administration
- Employee self-service
- Performance management
- Recruitment/onboarding
- Notifications
- Real-time collaboration
- Advanced reporting/custom report builders

## 6. Key Assumptions

* The application assumes a single authorized HR Manager as the user persona; no authentication or authorization mechanism is implemented.
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

## 8. Remaining Open Question

Deployment is the only remaining externally dependent decision: is there a preferred deployment environment, or is any publicly accessible deployment acceptable?

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

