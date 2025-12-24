---
name: memogarden-api-endpoint
description: Workflow for creating new API endpoints in MemoGarden Core. Use when adding new API routes, implementing CRUD operations, or extending the API surface.
---

# Writing a New API Endpoint

## Workflow

Follow this step-by-step workflow when creating a new API endpoint:

### 1. Define Pydantic Schemas

Create request/response schemas in `memogarden_core/api/v1/schemas/`:

```python
# memogarden_core/api/v1/schemas/entity.py
from pydantic import BaseModel, Field
from schema.types import Timestamp

class EntityCreate(BaseModel):
    """Schema for creating a new entity."""
    entity_type: str = Field(..., description="Type of entity (e.g., 'transactions')")
    group_id: str | None = Field(None, description="Optional group identifier")
    derived_from: str | None = Field(None, description="Parent entity ID if derived")

class EntityResponse(BaseModel):
    """Schema for entity response."""
    id: str
    entity_type: str
    group_id: str | None
    derived_from: str | None
    superseded_by: str | None
    created_at: Timestamp
    updated_at: Timestamp
```

### 2. Write the Endpoint

Create or edit the endpoint file in `memogarden_core/api/v1/`:

```python
from flask import Blueprint, jsonify
from api.validation import validate_request
from api.v1.schemas.entity import EntityCreate, EntityResponse
from db import get_core

router = Blueprint('entities', __name__)

@router.post("")
@validate_request
def create_entity(data: EntityCreate):
    """Create a new entity.

    Args:
        data: Validated EntityCreate instance from request body

    Returns:
        JSON response with created entity data, 201 status
    """
    with get_core(atomic=True) as core:
        entity_id = core.entity.create(
            entity_type=data.entity_type,
            group_id=data.group_id,
            derived_from=data.derived_from
        )
        entity = core.entity.get_by_id(entity_id)

    return jsonify(EntityResponse(**entity).model_dump()), 201
```

### 3. Register the Router

Register the blueprint in [main.py](../../memogarden/memogarden-core/memogarden_core/main.py):

```python
from api.v1.entities import router as entities_router

app.register_blueprint(entities_router, url_prefix=f"{settings.api_v1_prefix}/entities")
```

### 4. Write Tests

Create tests in `tests/api/`:

```python
def test_create_entity(client):
    """Test creating a new entity."""
    response = client.post("/api/v1/entities", json={
        "entity_type": "transactions"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data
    assert data["entity_type"] == "transactions"

def test_create_entity_missing_type(client):
    """Test creating entity without required field."""
    response = client.post("/api/v1/entities", json={})
    assert response.status_code == 400
```

## Key Patterns

### @validate_request Decorator

The `@validate_request` decorator uses type annotations to validate request bodies:

```python
@router.post("")
@validate_request
def create_endpoint(data: YourSchema):
    # data is already validated YourSchema instance
    ...
```

**Path parameters** (e.g., `<uuid>`) are automatically detected and passed as strings.

### Partial Update Pattern

For UPDATE endpoints, use `exclude_unset=True`:

```python
@router.patch("/<uuid>")
@validate_request
def update_entity(uuid: str, data: EntityUpdate):
    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        core.entity.update(uuid, update_data)
    ...
```

This allows updating only the fields that were actually provided in the request.

### Core API Usage

Use `get_core(atomic=True)` for multi-operation transactions:

```python
with get_core(atomic=True) as core:
    # Multiple operations that commit together
    entity_id = core.entity.create("transactions")
    core.transaction.create(entity_id, amount=100, ...)
    # All commit on __exit__, or rollback on error
```

Use `get_core()` (atomic=False) for single operations:

```python
core = get_core()
entity = core.entity.get_by_id(uuid)
# Connection closes automatically
```

## Best Practices

1. **Use atomic mode** for operations that modify multiple tables
2. **Return proper HTTP status codes**: 201 for created, 200 for OK, 404 for not found
3. **Include resource location** in Location header for 201 responses
4. **Validate input** using Pydantic schemas
5. **Handle errors** gracefully with meaningful error messages
6. **Write tests** before or alongside the endpoint
7. **Use module-level imports** for first-party modules:
   ```python
   from db import get_core  # ✅ PREFERRED
   from db.get_core import get_core  # ❌ AVOID
   ```

For detailed technical patterns and architecture, see [memogarden-core/docs/architecture.md](../../memogarden/memogarden-core/docs/architecture.md).
