# TODO List

## Email Service

- Added `ServiceError` exception for better error handling in services.

```python
# In email_service.py
except Exception as e:
    logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
    raise ServiceError("email", "Failed to send email", str(e))
```

## Settings Validation

- Replace `ValueError` with `InvalidConfigurationError` in settings validation.

```python
@field_validator('STRICT_VALIDATION')
def validate_strict_validation(cls, v):
    if v is True:
        raise InvalidConfigurationError(
            "STRICT_VALIDATION", 
            "Must be False in development environment. Please check your configuration."
        )
    return v
```

## Schema Validation

- Added `ValidationError` for schema validation. Use it in schema validators instead of `ValueError`.

