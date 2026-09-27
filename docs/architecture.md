Decision 1

Modular monolith over microservices

Reason: scale and domain complexity don't justify distributed operational complexity.

Decision 2

Relational database

Reason: salary data is structured, relational, transactional, and aggregation-heavy.

Decision 3

Separate Employee and Compensation domains

Reason: employee identity and compensation have different lifecycles.

Decision 4

Database-side aggregation

Reason: minimize data transferred to the application layer and make analytical operations efficient.

Decision 5

Pagination

Reason: prevent unnecessary transfer/rendering of the full employee population.

Decision 6

Explicit domain capabilities instead of generic CRUD abstraction

Reason: optimize the system around HR workflows rather than database mechanics.

That last one is particularly strong for an assessment like this.
