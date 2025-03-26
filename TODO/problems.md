# Identified Problems in Reminder Backend

## Repository Pattern Missing

API endpoints contain direct SQLAlchemy queries instead of using repository classes.  
**Example**: In `app/api/endpoints/clients.py`, DB operations should be abstracted away.

---

## Business Logic Location

Business logic is often embedded in API endpoints rather than service classes.  
**Example**: In `reminders.py`, the reminder calculation logic should be moved to a service.

---

## Error Handling

Inconsistent error handling across different modules:

- Some use `try/except` with custom exceptions.  
- Others return boolean success/failure.  

**Recommendation**: Standardize on one approach (custom exceptions preferred).

---

## Database Management

### Migrations

Alembic is set up, but `Base.metadata.create_all(bind=engine)` is still used in `main.py`.  
**Recommendation**: Rely entirely on migrations for schema management.

---

## Data Validation

The `STRICT_VALIDATION` toggle is a good feature, but validation bypassing could be more systematically implemented.

---

## Data Management & Performance

### Database Indexes

Some potentially high-volume tables, like `notifications`, could benefit from additional indexes.  
**Recommendation**: Analyze query patterns and add indexes accordingly.

### Bulk Operations

Some operations involving many records don't use bulk DB operations.  
**Example**: `bulk_import_clients` could use bulk inserts.
