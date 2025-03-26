# Database Architecture & ORM Best Practices

This document outlines the database architecture, ORM configuration, and best practices for the Reminder App backend.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Database Configuration](#database-configuration)
- [Connection Pooling](#connection-pooling)
- [Model Relationships](#model-relationships)
- [Migrations](#migrations)
- [Performance Optimization](#performance-optimization)
- [Maintenance Tasks](#maintenance-tasks)

## Architecture Overview

The Reminder App uses a layered database architecture:

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│   API Layer    │────▶│ Service Layer  │────▶│ Repository Layer│
└────────────────┘     └────────────────┘     └────────────────┘
                                                       │
                                                       ▼
                                              ┌────────────────┐
                                              │   ORM Layer    │
                                              └────────────────┘
                                                       │
                                                       ▼
                                              ┌────────────────┐
                                              │   Database     │
                                              └────────────────┘
```

- **API Layer**: Handles HTTP requests and responses
- **Service Layer**: Implements business logic
- **Repository Layer**: Handles data access patterns and abstracts database operations
- **ORM Layer**: SQLAlchemy models and core functionality
- **Database**: MySQL database (AWS RDS in production)

## Database Configuration

The database configuration is environment-specific and managed through settings files:

- `app/core/settings/base.py`: Base settings (shared across environments)
- `app/core/settings/development.py`: Development environment settings
- `app/core/settings/testing.py`: Testing environment settings
- `app/core/settings/production.py`: Production environment settings

The database connection is established in `app/database.py` with optimized connection pooling.

## Connection Pooling

Connection pooling is critical for production performance. Our implementation includes:

```python
engine_args = {
    "pool_pre_ping": True,  # Connection health checks
    "pool_recycle": 3600,   # Recycle connections after 1 hour
    "pool_size": 10,        # Default connection pool size
    "max_overflow": 20,     # Additional connections when pool is full
    "pool_timeout": 30,     # Wait time for connection when pool is full
}
```

### Key Configuration Parameters:

- **pool_pre_ping**: Tests connections before use to detect stale connections
- **pool_recycle**: Prevents using connections that have been idle for too long
- **pool_size**: Base number of connections to keep open
- **max_overflow**: Additional connections allowed beyond pool_size during high load
- **pool_timeout**: How long to wait for a connection when the pool is fully utilized

### Production Recommendations:

- For AWS RDS, set `pool_size` to approximately 10-20% of the maximum connections allowed
- Monitor connection usage during peak loads to adjust `max_overflow` appropriately
- Set `pool_recycle` to less than the database's connection timeout setting

## Model Relationships

SQLAlchemy model relationships should follow these best practices:

1. **Always define bidirectional relationships**: Use `relationship()` with `back_populates` 
2. **Cascade delete for parent-child relationships**: Use `cascade="all, delete-orphan"` for one-to-many relationships
3. **Use lazy loading appropriately**: Default is `lazy="select"`, but consider `lazy="joined"` for commonly accessed relationships
4. **Define constraints at the database level**: Use `UniqueConstraint`, `CheckConstraint`, etc.

### Example Pattern:

```python
# Parent model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    # ...
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")

# Child model
class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # ...
    user = relationship("User", back_populates="reminders")
```

### Validation Script

Use the validation script to check for relationship issues:

```bash
python -m scripts.verify_db_relationships
```

## Migrations

Database migrations are managed with Alembic:

### Creating Migrations

```bash
# Using our improved script (recommended):
python -m scripts.init_migrations --env development

# Or directly with Alembic:
alembic revision --autogenerate -m "Description of changes"
```

### Applying Migrations

```bash
# Apply all pending migrations:
alembic upgrade head

# Apply specific migration:
alembic upgrade <revision_id>

# Downgrade to previous migration:
alembic downgrade -1
```

### Best Practices:

1. **Always review auto-generated migrations** before applying them
2. **Test migrations** in development environment before production
3. **Back up the database** before applying migrations in production
4. **Include data migrations** when needed, not just schema changes

## Performance Optimization

### Query Optimization:

1. **Use specific queries** instead of loading entire objects when possible
2. **Eager load related objects** when you know you'll need them:
   ```python
   db.query(User).options(joinedload(User.reminders)).filter_by(id=user_id).first()
   ```
3. **Use pagination** for large result sets:
   ```python
   query = db.query(Reminder).filter_by(user_id=user_id)
   page = query.offset((page_num - 1) * per_page).limit(per_page).all()
   ```
4. **Add indexes** for frequently filtered columns

### Avoiding N+1 Query Problems:

The N+1 query problem occurs when you load a parent object and then separately load each of its children:

```python
# BAD: Will execute N+1 queries
users = db.query(User).all()
for user in users:
    # This will execute a separate query for each user
    reminders = user.reminders
```

Instead, use eager loading:

```python
# GOOD: Will execute only 1 or 2 queries
users = db.query(User).options(joinedload(User.reminders)).all()
for user in users:
    # Already loaded, no additional queries
    reminders = user.reminders
```

## Maintenance Tasks

Regular database maintenance tasks should include:

1. **Health monitoring**:
   ```bash
   python -m scripts.db_health_check --env production --output health_report.json
   ```

2. **Analyzing slow queries**:
   - Enable slow query logging in MySQL
   - Periodically review and optimize

3. **Index optimization**:
   - Analyze query patterns
   - Add or remove indexes as needed

4. **Connection pool monitoring**:
   - Watch for connection exhaustion
   - Adjust pool parameters based on usage patterns

5. **Regular backups**:
   - Automated daily backups
   - Test restoration procedures regularly 