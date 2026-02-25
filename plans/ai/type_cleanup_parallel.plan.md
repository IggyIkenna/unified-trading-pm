---
name: Instruments-Service Type Cleanup (Parallel Execution)
overview: Fix remaining 396 basedpyright errors across instruments-service using parallel agents. Builds on Session 2 success (processors now type-clean). Target: 0 errors across all files.
todos:
  - id: fix-orchestrator-types
    content: "Fix orchestrator.py type errors (328 errors → 0)"
    status: pending
  - id: fix-aggregator-types
    content: "Fix aggregator.py type errors (47 errors → 0)"
    status: pending
  - id: fix-handler-types
    content: "Fix handler type errors: instrument_handler.py (13), live_mode_handler.py (8)"
    status: pending
  - id: verify-all-clean
    content: "Run basedpyright on all files, verify 0 errors"
    status: pending
  - id: update-documentation
    content: "Update QUALITY_GATE_BYPASS_AUDIT.md with final exceptions"
    status: pending
  - id: commit-type-cleanup
    content: "Commit type cleanup with quickmerge"
    status: pending
isProject: false
---

# Instruments-Service Type Cleanup - Parallel Agent Plan

**Created**: 2026-02-23  
**Baseline**: Session 2 completed - processors are type-clean (0 errors)  
**Remaining**: 396 errors across 4 files  
**Target**: 0 errors across ALL files  
**Estimated Time**: 3-4 hours with 3 parallel agents

---

## 📍 QUICK START (For New Agents)

### Step 1: Read Context (5 minutes)

**Required Reading** (in order):
1. **This plan** (you're reading it)
2. `.cursor/plans/TYPE_FIXING_FINAL_REPORT.md` - What's already done (39 errors fixed)
3. `.cursor/plans/TYPE_FIXES_EXPLANATION.md` - How we fixed processors (patterns to replicate)
4. `.cursor/plans/SESSION_2_COMPLETION_STATUS.md` - Overall refactoring status

**Optional** (if confused):
5. `.cursor/plans/REFACTORING_STATUS_CHECKPOINT.md` - Full history
6. `.cursor/plans/PROCESSOR_ANALYSIS.md` - Processor implementation details

### Step 2: Claim Your File (1 minute)

Pick ONE file from work allocation (see below):
- **Agent 1**: orchestrator.py (hardest, 2-3 hours)
- **Agent 2**: aggregator.py (medium, 1 hour)
- **Agent 3**: handlers (easiest, 30 minutes)

### Step 3: Follow Pattern (2-3 hours per file)

See "Pattern Library" section below for proven fixes.

### Step 4: Verify (15 minutes)

```bash
# Your file should have 0 errors
basedpyright instruments_service/<your-file>.py --level warning
# 0 errors, 0 warnings, 0 notes

# Tests should pass
pytest tests/unit/ -q
# All passing
```

---

## 🎯 WORK ALLOCATION (3 Parallel Agents)

### Agent 1: orchestrator.py (328 errors) - HARDEST

**File**: `instruments_service/engine/operations/instruments/orchestrator.py`  
**Size**: 1119 lines  
**Errors**: 328 (82.8% of total)  
**Estimate**: 2-3 hours  
**Complexity**: HIGH (largest file, most errors)

**Error Breakdown**:
- reportUnknownMemberType: ~150
- reportUnknownVariableType: ~120
- reportAny: ~50
- Others: ~8

**Strategy**:
1. Remove `@handle_api_errors` decorators (if any)
2. Fix UMI adapter return types (get_adapter() returns untyped)
3. Add explicit type annotations for ALL variables
4. Fix dict[str, Any] from API responses
5. Work top-to-bottom, fix in chunks of 50 errors

### Agent 2: aggregator.py (47 errors) - MEDIUM

**File**: `instruments_service/engine/operations/aggregate/aggregator.py`  
**Size**: ~200 lines (estimate)  
**Errors**: 47 (11.9% of total)  
**Estimate**: 1 hour  
**Complexity**: MEDIUM

**Strategy**:
1. Same patterns as orchestrator (smaller scale)
2. Fix decorator issues
3. Explicit type annotations
4. Should be straightforward after seeing Agent 1's work

### Agent 3: handlers (21 errors) - EASIEST

**Files**:
- `cli/handlers/instrument_handler.py` (13 errors)
- `cli/handlers/live_mode_handler.py` (8 errors)

**Estimate**: 30 minutes  
**Complexity**: LOW

**Strategy**:
1. Handler delegation patterns
2. Fix method signatures
3. Quick wins

---

## 📚 PATTERN LIBRARY (Proven Fixes from Session 2)

### Pattern 1: Remove Untyped Decorators

**Problem**:
```python
from unified_cloud_services import handle_api_errors

@handle_api_errors(max_retries=3)  # ← Obscures types
async def fetch_data() -> tuple[dict, int]:
    return await api_call()
```

**Solution**:
```python
async def fetch_data() -> tuple[dict[str, Any], int]:
    max_retries: int = self.processing_config.retry_max_attempts
    last_error: Exception | None = None
    
    for attempt in range(max_retries):
        try:
            return await api_call()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                backoff_multiplier: int = cast(int, 2 ** attempt)
                backoff: float = self.processing_config.retry_backoff_factor * float(backoff_multiplier)
                logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
            else:
                raise Exception(f"Failed after {max_retries} retries") from last_error
    
    raise Exception("Unexpected: retry loop completed")
```

**Impact**: Fixes 20+ cascading errors per method

### Pattern 2: Explicit Variable Typing

**Problem**:
```python
for item in items:  # item is Unknown
    result = process(item)  # result is Unknown
```

**Solution**:
```python
for item in items:
    item_typed: dict[str, Any] = item  # Explicit type
    result: ProcessedData = process(item_typed)
```

### Pattern 3: Fix UMI Adapter Returns

**Problem**:
```python
from unified_market_interface import get_adapter

adapter = get_adapter("tardis")  # Returns untyped adapter
instruments = adapter.fetch_instruments()  # Unknown return
```

**Solution**:
```python
from unified_market_interface import get_adapter
from unified_market_interface.adapters.tradfi import TardisAdapter

adapter_generic = get_adapter("tardis")
adapter: TardisAdapter = cast(TardisAdapter, adapter_generic)  # Explicit type
instruments: dict[str, dict[str, Any]] = adapter.fetch_instruments()
```

### Pattern 4: Fix dict[str, Any] Iterations

**Problem**:
```python
for key, value in my_dict.items():  # key/value are Unknown
    process(value)
```

**Solution**:
```python
for key, value in my_dict.items():
    key_str: str = str(key)
    value_dict: dict[str, Any] = cast(dict[str, Any], value)
    process(value_dict)
```

### Pattern 5: Protocol Variance (When Unavoidable)

**Problem**:
```python
def call_protocol_function(service: MyProtocol):
    pass

call_protocol_function(self)  # Error: concrete types incompatible
```

**Solution**:
```python
call_protocol_function(self)  # type: ignore[reportArgumentType]  # Protocol variance with mutable attributes
```

**Document**: Add comment explaining why this specific exception is needed

---

## 🚀 EXECUTION STRATEGY

### Phase 1: Parallel Execution (3 agents, 2-3 hours)

```
Agent 1 (hardest):  orchestrator.py (328 errors)
Agent 2 (medium):   aggregator.py (47 errors)
Agent 3 (easiest):  handlers (21 errors)
```

**Start simultaneously** - no dependencies between files

### Phase 2: Verification (15 minutes, sequential)

After all agents complete:
```bash
# Agent 4 or original agent
cd instruments-service && source .venv/bin/activate

# Check each file
basedpyright instruments_service/engine/operations/instruments/orchestrator.py --level warning
basedpyright instruments_service/engine/operations/aggregate/aggregator.py --level warning
basedpyright instruments_service/cli/handlers/*.py --level warning

# Check full directory
basedpyright instruments_service/ --level warning
# Target: 0 errors, 0 warnings (except reportMissingImports for path deps)
```

### Phase 3: Documentation (15 minutes)

Update `docs/QUALITY_GATE_BYPASS_AUDIT.md`:
- List final essential exceptions (should be <5 total)
- Document why each cannot be fixed
- Reference PEP 544, context7 research

### Phase 4: Commit (30 minutes)

```bash
bash scripts/quality-gates.sh --no-fix
# Should pass with Types: ✅ PASSED

bash scripts/quickmerge.sh "Fix all type errors: processors + orchestrator + aggregator (435→0 errors)"
```

---

## 📋 AGENT-SPECIFIC INSTRUCTIONS

### Agent 1: orchestrator.py

**Context Files to Read**:
1. This plan (work allocation section)
2. `.cursor/plans/TYPE_FIXES_EXPLANATION.md` (Pattern 1: decorator removal)
3. cefi_processor.py (reference implementation)

**Your Task**:
1. Find all `@handle_api_errors` decorators → replace with manual retry
2. Find all `get_adapter()` calls → add explicit type casts
3. Find all dict iterations → add type annotations
4. Work methodically: fix 50 errors, test, continue

**Checkpoints** (verify every 50 errors):
```bash
basedpyright orchestrator.py --level warning | grep "error:" | wc -l
# Should decrease: 328 → 278 → 228 → ...
```

**Success**: 0 errors in orchestrator.py

### Agent 2: aggregator.py

**Context Files to Read**:
1. This plan (work allocation section)
2. `.cursor/plans/TYPE_FIXES_EXPLANATION.md` (all patterns)
3. orchestrator.py (after Agent 1 finishes - reference similar patterns)

**Your Task**:
1. Apply same patterns as orchestrator.py (smaller scale)
2. Remove decorators
3. Explicit types
4. Test frequently

**Success**: 0 errors in aggregator.py

### Agent 3: handlers

**Context Files to Read**:
1. This plan (work allocation section)
2. Pattern 2 and 3 from Pattern Library above

**Your Task**:
1. Fix method signatures
2. Add type annotations for handler delegation
3. Quick wins - should be straightforward

**Files**:
- `cli/handlers/instrument_handler.py` (13 errors)
- `cli/handlers/live_mode_handler.py` (8 errors)

**Success**: 0 errors in both handlers

---

## ⚠️ COORDINATION

### Avoid Conflicts

**Different files = Zero conflicts**:
- Agent 1: orchestrator.py
- Agent 2: aggregator.py
- Agent 3: handlers/*.py

**No shared code** - safe to work in parallel

### If You Need to Edit Same File

**Unlikely** - files are independent

**If needed**: Coordinate via plan updates (mark your agent ID)

---

## ✅ SUCCESS CRITERIA

### Per-File Success:
- [ ] orchestrator.py: 0 errors ✅
- [ ] aggregator.py: 0 errors ✅
- [ ] instrument_handler.py: 0 errors ✅
- [ ] live_mode_handler.py: 0 errors ✅

### Overall Success:
```bash
basedpyright instruments_service/ --level warning
# 0 errors (except reportMissingImports - acceptable)
```

### Test Success:
```bash
pytest tests/unit/ -q
# All passing ✅
```

### Quality Gates:
```bash
bash scripts/quality-gates.sh --no-fix
# Types: ✅ PASSED
```

---

## 📊 BASELINE (Session 2 Complete)

### Already Fixed (39 errors):
- ✅ cefi_processor.py: 22 → 0
- ✅ tradfi_processor.py: 4 → 0
- ✅ events.py: 1 → 0
- ✅ main.py: 2 → 0
- ✅ instruments_service.py: 3 → 0
- ✅ instrument_processing_service.py: 7 → improved

### Remaining (396 errors):
- ⏳ orchestrator.py: 328 (Agent 1)
- ⏳ aggregator.py: 47 (Agent 2)
- ⏳ instrument_handler.py: 13 (Agent 3)
- ⏳ live_mode_handler.py: 8 (Agent 3)

---

## 🔧 COMMON PITFALLS (Avoid These)

### ❌ Don't Do This:

1. **Don't just add type: ignore everywhere**
   - Fix the root cause
   - Only ignore when LITERALLY cannot fix (Protocol variance, __getattr__)

2. **Don't break tests**
   - Run `pytest tests/unit/ -q` after every 50 errors fixed
   - Verify imports work: `python -c "from instruments_service.engine.operations.instruments.orchestrator import InstrumentsOrchestrator"`

3. **Don't skip verification**
   - Check error count decreases after each fix
   - Run basedpyright frequently: `basedpyright <file> --level warning | grep "error:" | wc -l`

4. **Don't fix other files**
   - Stay in your assigned file(s)
   - Avoid merge conflicts

### ✅ Do This:

1. **Follow the patterns** from TYPE_FIXES_EXPLANATION.md
2. **Test frequently** (every 50 errors or 15 minutes)
3. **Document unavoidable exceptions** with clear comments
4. **Verify basedpyright shows improvement** after each batch

---

## 📁 FILE LOCATIONS

### Plans (Read These):
- **This plan**: `.cursor/plans/type_cleanup_parallel.plan.md`
- **Type fixing report**: `.cursor/plans/TYPE_FIXING_FINAL_REPORT.md`
- **Fix explanations**: `.cursor/plans/TYPE_FIXES_EXPLANATION.md`
- **Session 2 status**: `.cursor/plans/SESSION_2_COMPLETION_STATUS.md`

### Code (Fix These):
- **orchestrator.py**: `instruments_service/engine/operations/instruments/orchestrator.py`
- **aggregator.py**: `instruments_service/engine/operations/aggregate/aggregator.py`
- **Handlers**: `instruments_service/cli/handlers/instrument_handler.py`, `live_mode_handler.py`

### Reference (Working Examples):
- **cefi_processor.py**: `instruments_service/engine/operations/instruments/processors/cefi_processor.py` (0 errors ✅)
- **tradfi_processor.py**: `instruments_service/engine/operations/instruments/processors/tradfi_processor.py` (0 errors ✅)

---

## 🔍 ERROR ANALYSIS (Before Starting)

### Check Your File First:

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service
source .venv/bin/activate

# See errors in your file
basedpyright instruments_service/engine/operations/instruments/orchestrator.py --level warning 2>&1 | less

# Count by error type
basedpyright orchestrator.py --level warning 2>&1 | grep -o "report[A-Za-z]*" | sort | uniq -c | sort -rn
```

**Expected Output**:
```
150 reportUnknownMemberType
120 reportUnknownVariableType
 50 reportAny
  8 reportArgumentType
```

### Error Type Guide:

| Error Type | Meaning | Typical Fix |
|------------|---------|-------------|
| reportUnknownMemberType | Method/attribute type unknown | Add type annotation or cast |
| reportUnknownVariableType | Variable type unknown | Add explicit type: `var: type = ...` |
| reportAny | Using Any type | Use specific type or document exception |
| reportArgumentType | Wrong argument type | Fix type or add cast |
| reportMissingImports | Import not resolved | Add `# type: ignore[reportMissingImports]` |

---

## 🎓 PATTERN LIBRARY (Copy-Paste Ready)

### Pattern 1: Remove @handle_api_errors Decorator

**Find**:
```python
@handle_api_errors(max_retries=3)
async def my_method(self, arg1: str) -> ReturnType:
    return await some_call(arg1)
```

**Replace With**:
```python
async def my_method(self, arg1: str) -> ReturnType:
    max_retries: int = self.processing_config.retry_max_attempts
    last_error: Exception | None = None
    
    for attempt in range(max_retries):
        try:
            return await some_call(arg1)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                backoff_multiplier: int = cast(int, 2 ** attempt)
                backoff: float = self.processing_config.retry_backoff_factor * float(backoff_multiplier)
                logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
            else:
                raise Exception(f"Failed after {max_retries} retries") from last_error
    
    raise Exception("Unexpected: retry loop completed")
```

**Imports Needed**:
```python
import asyncio
from typing import cast
```

### Pattern 2: Fix get_adapter() Return Types

**Find**:
```python
from unified_market_interface import get_adapter

adapter = get_adapter("tardis")  # Unknown type
result = adapter.fetch_instruments(...)  # Unknown return
```

**Replace With**:
```python
from unified_market_interface import get_adapter
from unified_market_interface.adapters.tradfi import TardisAdapter

adapter_generic = get_adapter("tardis")
adapter: TardisAdapter = cast(TardisAdapter, adapter_generic)
result: dict[str, dict[str, Any]] = adapter.fetch_instruments(...)
```

### Pattern 3: Fix Dict Iterations

**Find**:
```python
for key, value in my_dict.items():  # key/value are Unknown
    process(value)
```

**Replace With**:
```python
for key, value in my_dict.items():
    key_str: str = str(key)
    value_data: dict[str, Any] = cast(dict[str, Any], value)
    process(value_data)
```

### Pattern 4: Fix API Response Types

**Find**:
```python
response = await api_call()  # Unknown type
data = response.get("data")  # Unknown type
```

**Replace With**:
```python
response: dict[str, Any] = await api_call()
data: list[dict[str, Any]] | None = response.get("data")
if data is not None:
    for item in data:
        item_typed: dict[str, Any] = item
```

### Pattern 5: Fix Method Return Types

**Find**:
```python
def my_method(self, arg):  # Missing types
    result = process(arg)
    return result
```

**Replace With**:
```python
def my_method(self, arg: str) -> dict[str, Any]:
    result: dict[str, Any] = process(arg)
    return result
```

---

## 🧪 VERIFICATION CHECKLIST

### After Each Batch of Fixes (Every 50 Errors):

```bash
# 1. Check error count decreased
basedpyright <your-file>.py --level warning 2>&1 | grep "error:" | wc -l
# Should be lower than before

# 2. Check imports work
python -c "from instruments_service.<your-module> import <YourClass>; print('✅ OK')"

# 3. Run related tests
pytest tests/unit/test_<your-module>.py -v
```

### Before Marking Complete:

```bash
# 1. Zero errors in your file
basedpyright <your-file>.py --level warning
# 0 errors, 0 warnings, 0 notes

# 2. All tests pass
pytest tests/unit/ -q
# X passed, Y skipped (no failures)

# 3. Code runs
python -c "from instruments_service.<your-module> import <YourClass>; obj = <YourClass>({}); print('✅ Runtime OK')"
```

### Final Verification (All Agents Done):

```bash
# All files clean
basedpyright instruments_service/ --level warning
# 0 errors (except reportMissingImports - acceptable)

# Quality gates pass
bash scripts/quality-gates.sh --no-fix
# Types: ✅ PASSED
```

---

## 📝 DOCUMENTATION REQUIREMENTS

### For Each Essential Exception:

Add to your file with clear comment:
```python
# Example:
enhanced_fields = await populate_derived_fields(
    service=self,  # type: ignore[reportArgumentType]  # Protocol variance: CeFiInstrumentProcessor has concrete types (VenueMapping, ExchangeInstrumentConfig) but DerivedFieldsServiceProtocol expects object. Per PEP 544, mutable Protocol attributes must be invariant. Fixing requires Protocol refactor in derived_fields_populator.py (separate task).
    ...
)
```

### Update QUALITY_GATE_BYPASS_AUDIT.md:

Add section 2.1 entries:
```markdown
|| File | Line | Code | Purpose |
|------|------|------|---------|
|| `orchestrator.py` | 123 | `service=self  # type: ignore[reportArgumentType]` | Protocol variance |
|| `aggregator.py` | 45 | `result: Any  # type: ignore[reportAny]` | UMI adapter returns untyped |
```

**Rule**: Only document exceptions that CANNOT be fixed (Protocol variance, __getattr__, etc.)

---

## 🎯 ESTIMATED TIME

### Sequential (One Agent):
- orchestrator.py: 2-3 hours
- aggregator.py: 1 hour
- handlers: 30 minutes
- **Total**: 3.5-4.5 hours

### Parallel (3 Agents):
- All work simultaneously
- **Total**: 2-3 hours (longest agent)
- **Speedup**: ~2x faster

### With Verification & Commit:
- Parallel work: 2-3 hours
- Verification: 15 minutes
- Documentation: 15 minutes
- Commit: 30 minutes
- **Total**: 3-4 hours end-to-end

---

## 🔗 DEPENDENCIES

### Prerequisites (Already Done):
- ✅ Session 2 complete (processors type-clean)
- ✅ Dependencies installed (unified-config-interface, etc.)
- ✅ Circular imports fixed
- ✅ Tests passing (37/37)

### No Dependencies Between Agents:
- orchestrator.py ← Independent
- aggregator.py ← Independent
- handlers ← Independent

**Safe to parallelize** ✅

---

## 📞 IF YOU GET STUCK

### Common Issues:

**1. Error count not decreasing**:
- Check you're fixing the right thing
- Verify syntax: `python -c "import your_file"`
- One fix may create temporary errors (normal)

**2. Tests failing**:
- Revert last change
- Check imports still work
- Run single test: `pytest tests/unit/test_specific.py -v`

**3. Unclear how to fix an error**:
- Look at cefi_processor.py (reference)
- Check TYPE_FIXES_EXPLANATION.md (patterns)
- Search for similar errors: `grep -r "pattern" <file>`

### Get Help:

1. Read `.cursor/plans/TYPE_FIXES_EXPLANATION.md` again
2. Look at fixed files: cefi_processor.py, tradfi_processor.py
3. Check context7: Search for specific error pattern

---

## 🎉 EXPECTED OUTCOME

### After Completion:

**Type Errors**: 435 → **0** ✅  
**Files Clean**: ALL ✅  
**Tests Passing**: ALL ✅  
**Quality Gates**: PASS ✅  
**Refactoring**: 100% complete ✅

### Deliverable:

✅ Complete instruments-service refactoring
✅ 100% type-clean codebase
✅ Modern structure (engine/, adapters/)
✅ All quality gates passing
✅ Ready to replicate to other 13 services

---

## 🚀 START HERE

**For Agent Taking This On**:

1. **Read this plan** (5 min)
2. **Read TYPE_FIXING_FINAL_REPORT.md** (5 min)
3. **Claim your file** (comment in plan)
4. **Start fixing** (2-3 hours)
5. **Verify** (15 min)
6. **Mark complete** (update todos in this plan)

**Agents**: Launch 3 in parallel for 2x speedup!

**Location**: `/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/type_cleanup_parallel.plan.md`

---

## 📋 PROGRESS TRACKING

Update this section as you complete work:

- [ ] Agent 1: orchestrator.py (328 errors) - Status: Not started
- [ ] Agent 2: aggregator.py (47 errors) - Status: Not started  
- [ ] Agent 3: handlers (21 errors) - Status: Not started
- [ ] Verification: basedpyright full scan - Status: Pending
- [ ] Documentation: QUALITY_GATE_BYPASS_AUDIT.md - Status: Pending
- [ ] Commit: quickmerge - Status: Pending

**Overall**: 0% of type cleanup work, 90% of refactoring work
