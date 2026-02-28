# Coding Standards Enforcement - For Agent Prompts

**Purpose**: Key coding standards that ALL agents must follow  
**Updated**: 2026-02-23 (expanded with empty fallbacks, Type Any)  
**Used By**: Include in `AGENT_TASK_TEMPLATE.md` and all agent prompts

**Related**: 
- `AGENT_TASK_TEMPLATE.md` - Generic safeguards template (references this doc)
- `.cursor/rules/no-empty-fallbacks.mdc` - Cursor rule (expanded)
- `.cursor/rules/no-type-any-use-specific.mdc` - Cursor rule (new)

---

## 🚫 FORBIDDEN PATTERNS (NEVER DO THESE)

### 1. Empty Fallbacks (Fail Loud, Not Silent)

**Rule**: `.cursor/rules/no-empty-fallbacks.mdc`

```python
# ❌ BAD: Empty fallbacks hide errors
project_id = os.environ.get("GCP_PROJECT_ID", "")
config = self._config.get("service-config", {})
venues = settings.get("venues", [])

# Then defensive isinstance (even worse!):
if not isinstance(config, dict):
    config = {}

# ✅ GOOD: Fail loud with clear error
project_id = os.environ.get("GCP_PROJECT_ID")
if not project_id:
    raise ValueError("GCP_PROJECT_ID required. Set via .env file.")

config = self._config.get("service-config")
if config is None:
    raise ValueError("service-config is required in config file")
if not isinstance(config, dict):
    raise TypeError(f"service-config must be dict, got {type(config).__name__}")
```

**Why**: Empty fallbacks hide configuration errors. Error surfaces hours later with cryptic message. Developer wastes time debugging wrong layer.

---

### 2. Type Any (Use Specific Types)

**Rule**: `.cursor/rules/no-type-any-use-specific.mdc`, `.cursor/rules/strict-type-checking.mdc`

```python
# ❌ BAD: Any defeats type checking
from typing import Any

def process(data: Any) -> Any:
    return data.some_method()  # No type safety

result: dict[str, Any] = load_config()  # Lazy typing

# ✅ GOOD: Specific types (check source code!)
from pydantic import BaseModel

class ServiceConfig(BaseModel):
    max_workers: int
    batch_size: int

def process(data: pd.DataFrame) -> ProcessedData:
    return ProcessedData(df=data)

result: ServiceConfig = ServiceConfig(**load_config())
```

**Why**: You almost ALWAYS know the structure:
1. Check API docs
2. Look at source code (cross-repo dependencies)
3. Check tests for usage examples
4. Runtime inspect: `print(type(value), value)`

**Rule**: If you know ANY structure, don't use `Any`. Only acceptable for truly dynamic external APIs (document TODO to define schema).

---

### 3. Type object (Avoid Unless Truly Unknown)

```python
# ❌ BAD: Using object when you know it's a dict
def process_config(config: object) -> None:
    # You know it's dict - use dict type!
    pass

# ✅ GOOD: Specific type
def process_config(config: dict[str, str | int | bool]) -> None:
    # Now typed!
    pass

# ✅ OK (rare): Truly unknown nesting from external source
def serialize_unknown(value: object) -> str:
    """Serialize value of unknown type from external API."""
    return json.dumps(value, default=str)
```

**Rule**: `object` only when nesting level is **truly unknown** at compile time. This is rare - usually you know at least the top-level type.

---

### 4. dict[str, Any] (Minimize, Document When Used)

```python
# ❌ BAD: Internal config (you control the structure!)
def get_config() -> dict[str, Any]:
    return self._config

# ✅ GOOD: Define structure
from typing import TypedDict

class ServiceConfig(TypedDict):
    max_workers: int
    venues: list[str]
    batch_size: int

def get_config() -> ServiceConfig:
    return ServiceConfig(**self._config)

# ✅ ACCEPTABLE: External API (no schema available)
def fetch_external() -> dict[str, Any]:  # type: ignore[reportAny]
    """
    Fetch from third-party API with unknown schema.
    
    TODO: Define schema once API stabilizes (Issue #123)
    """
    return requests.get(...).json()
```

**Acceptable cases** (document with `# type: ignore[reportAny]` + comment):
1. Truly dynamic JSON from external API
2. Forwarding untyped data (middleware)
3. Temporary during migration (TODO to fix)

---

## 📋 QUALITY GATE CHECKS

### Add These Checks to scripts/quality-gates.sh:

```bash
#============================================================================
# STEP 5.5: NO EMPTY FALLBACKS (BLOCKING)
#============================================================================
echo -n "Checking for empty fallbacks... "

# Empty strings
EMPTY_STR=$(rg '\.get\(["\'][\w_-]+["\']\s*,\s*["\']["\']' --type py \
    --glob "!tests/**" --glob "!scripts/**" . 2>/dev/null || true)

# Empty dicts
EMPTY_DICT=$(rg '\.get\(["\'][\w_-]+["\']\s*,\s*\{\}' --type py \
    --glob "!tests/**" --glob "!scripts/**" . 2>/dev/null || true)

# Empty lists
EMPTY_LIST=$(rg '\.get\(["\'][\w_-]+["\']\s*,\s*\[\]' --type py \
    --glob "!tests/**" --glob "!scripts/**" . 2>/dev/null || true)

if [ -n "$EMPTY_STR" ] || [ -n "$EMPTY_DICT" ] || [ -n "$EMPTY_LIST" ]; then
    echo -e "${RED}FAIL${NC}"
    echo -e "${RED}Empty fallbacks found (must fail loud):${NC}"
    [ -n "$EMPTY_STR" ] && echo "$EMPTY_STR" | head -5
    [ -n "$EMPTY_DICT" ] && echo "$EMPTY_DICT" | head -5
    [ -n "$EMPTY_LIST" ] && echo "$EMPTY_LIST" | head -5
    echo -e "${RED}Fix: Replace .get('key', {}) with explicit validation${NC}"
    exit 1
fi
echo -e "${GREEN}PASS${NC}"

#============================================================================
# STEP 5.6: NO TYPE ANY (BLOCKING)
#============================================================================
echo -n "Checking for Type Any (use specific types)... "

ANY_USAGE=$(rg ': Any[^[]|-> Any[^[]|\[Any\]' --type py \
    --glob "!tests/**" --glob "!**/protocols.py" . 2>/dev/null | \
    grep -v "dict\[str, Any\]" | \
    grep -v "# type: ignore\[reportAny\]" || true)

if [ -n "$ANY_USAGE" ]; then
    echo -e "${RED}FAIL${NC}"
    echo -e "${RED}Type Any found (use specific types):${NC}"
    echo "$ANY_USAGE" | head -10
    echo -e "${RED}Check source code to determine actual type${NC}"
    exit 1
fi
echo -e "${GREEN}PASS${NC}"
```

---

## 🔍 EXAMPLES FOR AGENTS

### Example 1: Config Access Pattern

```python
# ❌ BAD (what user found):
features_config: dict[str, Any] = self._config.get("features-delta-one-service", {})
if not isinstance(features_config, dict):
    features_config = {}

# Problems:
# 1. Empty dict fallback (hides missing config)
# 2. Defensive isinstance (hides type errors)
# 3. Type Any (lazy typing)
# 4. Errors surface later ("KeyError: 'max_workers'")

# ✅ GOOD (fail loud, specific types):
from pydantic import BaseModel

class FeaturesConfig(BaseModel):
    max_workers: int = 16
    batch_size: int = 1000
    venues: list[str]

features_config_raw = self._config.get("features-delta-one-service")
if features_config_raw is None:
    raise ValueError(
        "features-delta-one-service config is required. "
        "Add to config file: {max_workers: 16, batch_size: 1000, venues: [...]}"
    )

if not isinstance(features_config_raw, dict):
    raise TypeError(
        f"features-delta-one-service must be dict, got {type(features_config_raw).__name__}. "
        "Check config file format."
    )

# Type narrowing + validation
features_config: FeaturesConfig = FeaturesConfig(**features_config_raw)
# Now fully typed with validation!
```

### Example 2: API Response Typing

```python
# ❌ BAD: Assume Any
response: dict[str, Any] = api_call()
data = response.get("data")  # Any type
for item in data:  # Unknown type
    process(item)  # No type safety

# ✅ GOOD: Define structure (check API docs or source code)
from typing import TypedDict

class ApiResponse(TypedDict):
    status: str
    data: list[dict[str, str]]
    count: int

response: ApiResponse = ApiResponse(**api_call())
data: list[dict[str, str]] = response["data"]  # Fully typed!
for item in data:
    item_typed: dict[str, str] = item
    process(item_typed)  # Type safe!
```

### Example 3: Cross-Repo Dependency Types

```python
# ❌ BAD: Assume unknown
from unified_trading_services import InstrumentsDomainClient

client = InstrumentsDomainClient(...)
result: Any = client.get_instruments_for_date(...)

# ✅ GOOD: Check unified-trading-services source code
# InstrumentsDomainClient.get_instruments_for_date returns pd.DataFrame

import pandas as pd

result: pd.DataFrame = client.get_instruments_for_date(...)
# Fully typed! Can use .columns, .iterrows(), etc. with type safety
```

---

## 📋 FOR ALL AGENT PROMPTS: Include These Standards

### Copy-Paste Block for Agent Prompts:

```
**CODING STANDARDS (CRITICAL)**:

1. NO EMPTY FALLBACKS (fail loud):
   - Never: .get("key", ""), .get("key", {}), .get("key", [])
   - Never: Defensive isinstance after .get with empty fallback
   - Always: Explicit validation with clear error messages
   
   Example:
   ❌ config = self._config.get("service", {})
   ❌ if not isinstance(config, dict): config = {}
   
   ✅ config = self._config.get("service")
   ✅ if config is None: raise ValueError("service config required")
   ✅ if not isinstance(config, dict): raise TypeError(f"Must be dict, got {type(config)}")

2. NO TYPE ANY (use specific types):
   - Check source code to determine actual type
   - Check API docs, tests, cross-repo dependencies
   - Use TypedDict/Pydantic for known structures
   - Only use Any for truly dynamic external APIs (document TODO)
   
   Example:
   ❌ result: dict[str, Any] = api_call()
   ✅ class ApiResponse(TypedDict): status: str; data: list[dict[str, str]]
   ✅ result: ApiResponse = ApiResponse(**api_call())

3. NO TYPE OBJECT (unless truly unknown):
   - Usually you know at least top-level type (dict, list, str)
   - object only for completely unknown nesting from external source
   
4. FAIL FAST VALIDATION:
   - Validate config in __init__, not 100 lines later
   - Clear error messages: what's missing + how to fix
   - No silent failures

References:
- .cursor/rules/no-empty-fallbacks.mdc
- .cursor/rules/no-type-any-use-specific.mdc
- .cursor/rules/strict-type-checking.mdc
```

---

## ✅ ENFORCEMENT

**Quality Gates Check** (add to scripts/quality-gates.sh):
- Empty string fallbacks: `.get("key", "")`
- Empty dict fallbacks: `.get("key", {})`
- Empty list fallbacks: `.get("key", [])`
- Type Any usage: `: Any`, `-> Any`
- Type object usage: `: object` (warning)

**Cursor Rules**:
- `.cursor/rules/no-empty-fallbacks.mdc` (expanded)
- `.cursor/rules/no-type-any-use-specific.mdc` (new)
- `.cursor/rules/strict-type-checking.mdc` (existing)

**basedpyright**:
- `reportAny: "error"` (catches Type Any)
- `reportUnknownVariableType: "error"` (catches vague types)

---

## 📊 IMPACT

**Before**:
- Code runs with empty dicts/strings
- Errors surface hours later
- Debugging wrong layer
- Type Any everywhere (no safety)

**After**:
- Code fails immediately with clear message
- Developer knows exactly what's missing
- Fix at config layer (correct place)
- Specific types (autocomplete, refactoring safety)

**This makes code**:
- ✅ Safer (catch errors early)
- ✅ Clearer (explicit expectations)
- ✅ Faster to debug (right layer)
- ✅ More maintainable (type safety)

---

**Include this block in ALL agent task prompts** ✅

**See also**: `AGENT_TASK_TEMPLATE.md` for complete agent task template (includes these standards)
