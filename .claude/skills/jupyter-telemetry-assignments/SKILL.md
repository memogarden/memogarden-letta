---
name: jupyter-telemetry-assignments
description: Assignment tagging workflow for Jupyter notebook telemetry. Covers how to tag notebook cells with assignment metadata for tracking student progress and assignment completion.
---

# Jupyter Telemetry Assignment Tagging

This skill guides the process of adding assignment tags to Jupyter notebooks for the Learning Analytics Platform.

## Purpose

Assignment tags enable the platform to:
- Track which specific exercises students are working on
- Detect when students are struggling with particular problems
- Calculate assignment completion rates
- Provide per-assignment error tracking (consecutive errors on same problem)
- Generate assignment-based signals (e.g., stuck on specific exercise)

## Tag Format

Assignment tags follow the pattern: `assignment:<lesson>-<exercise>`

**Examples:**
- `assignment:lesson-03-exercise-1` - Lesson 3, Exercise 1
- `assignment:lesson-06a-exercise-2` - Lesson 6a, Exercise 2
- `assignment:lesson-01-practice-1` - Lesson 1, Practice problem 1

**Naming conventions:**
- Use kebab-case (lowercase with hyphens)
- Include lesson number and exercise/problem identifier
- No spaces or special characters (URL-safe)
- Keep descriptive but concise

## How to Add Tags

### Method 1: Jupyter Notebook UI

1. Open the notebook in Jupyter (Classic Notebook 6.x)
2. Select the code cell you want to tag
3. Go to **View > Cell Toolbar > Tags**
4. Click **Add Tag** in the cell's tag panel
5. Type `assignment:<lesson>-<exercise>` (e.g., `assignment:lesson-01-exercise-1`)
6. Press Enter to save the tag

### Method 2: JSON Editing

1. Open the `.ipynb` file in a text editor
2. Find the code cell to tag (look for exercise functions or problem statements)
3. Add metadata to the cell:

```json
{
  "cell_type": "code",
  "metadata": {
    "tags": ["assignment:lesson-01-exercise-1"]
  },
  "source": [
    "def your_function():\n",
    "    # Your code here\n",
    "    pass\n"
  ]
}
```

### Method 3: Programmatic (Python)

For batch tagging multiple cells:

```python
import json

with open("lesson_xx.ipynb", "r") as f:
    nb = json.load(f)

# Tag specific cells by index
cells_to_tag = [
    (10, "assignment:lesson-xx-exercise-1"),
    (15, "assignment:lesson-xx-exercise-2"),
]

for cell_idx, tag in cells_to_tag:
    cell = nb["cells"][cell_idx]
    if "metadata" not in cell:
        cell["metadata"] = {}
    if "tags" not in cell["metadata"]:
        cell["metadata"]["tags"] = []
    if tag not in cell["metadata"]["tags"]:
        cell["metadata"]["tags"].append(tag)

with open("lesson_xx.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
```

## Which Cells Should Be Tagged?

**Tag these cells:**
- Exercise implementations (functions students need to write)
- Problem-solving code cells
- Challenge questions
- Graded assignments

**Don't tag these:**
- Explanation/example code cells
- "Try this" practice cells (unless they're specific exercises)
- Markdown cells (they won't execute code anyway)
- Solution/demonstration cells

## Currently Tagged Notebooks

| Notebook | Tagged Cells | Tag IDs |
|----------|--------------|---------|
| `lesson_03.ipynb` | 1 | `assignment:lesson-03-exercise-1` |
| `lesson_06a.ipynb` | 2 | `assignment:lesson-06a-exercise-1`, `assignment:lesson-06a-exercise-2` |

## Testing Assignment Detection

To verify tags are working:

1. Start the JupyterHub with telemetry enabled
2. Open a tagged notebook
3. Execute a tagged cell
4. Check the events table:

```sql
SELECT
    actor,
    verb,
    object->>'assignment' as assignment,
    created_at
FROM events
WHERE object->>'assignment' IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;
```

You should see `assignment` field populated with the tag value.

## Technical Details

### How Detection Works

1. **custom.js** (`/jupyterhub/custom/custom.js`) checks cell metadata on execute
2. `getAssignmentTag()` function looks for tags starting with `assignment:`
3. Tag is included in telemetry event payload as `object.assignment`
4. Dashboard stores assignment in `events` table (JSONB field)
5. Signal service uses assignment for consecutive_errors detection

### Relevant Code Locations

- **Telemetry injection:** `/jupyterhub/custom/custom.js` (lines 112-127, 220-261)
- **Database schema:** Events table with `object` JSONB column
- **Signal detection:** `/dashboard/services/signal_service.py` (consecutive_errors)

## Integration with Signal Detection

Assignment tags are used by these signals:

1. **consecutive_errors:** Tracks identical errors on same assignment
   - Groups by `session_id`, `object_id`, and `assignment`
   - Requires 3+ consecutive errors with same `code_hash`

2. **Future enhancements:**
   - Assignment completion rate tracking
   - Per-assignment time spent
   - Assignment-specific struggle detection

## Workflow Summary

1. Identify notebook with exercises to tag
2. Determine tag names for each exercise
3. Add tags using one of the methods above
4. Test by executing tagged cells in JupyterHub
5. Verify events have `assignment` field populated
6. Commit changes to programming-in-python repository
