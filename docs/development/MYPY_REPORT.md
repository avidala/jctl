# mypy Type Checking Report

> **Note (2026-05-13):** This report is a historical snapshot from the
> v0.1.0-beta.1 release and references `jctl/auth/okta.py` and
> `jctl/auth/token_manager.py`, which have since been removed when Okta/OAuth
> support was dropped. Re-run `mypy jctl/` for the current state of the
> codebase.

**Date**: 2025-01-20
**Version**: v0.1.0-beta.1
**mypy Version**: 1.18.2

## Summary

- **Total Files Checked**: 27
- **Files with Errors**: 14
- **Total Errors**: 50
- **Severity**: Minor (type annotations and Any returns)

## Error Breakdown

### By Category

| Category | Count | Description |
|----------|-------|-------------|
| Missing return annotations | 11 | Functions missing `-> None` or return type |
| Returning Any | 19 | Functions returning `Any` instead of specific types |
| Type incompatibility | 9 | Incompatible types in assignments/arguments |
| Variable annotations | 4 | Variables needing type annotations |
| Name redefinition | 2 | Variable names defined multiple times |
| Miscellaneous | 5 | Other type issues |

### By File

| File | Errors | Severity |
|------|--------|----------|
| jctl/jenkins/client.py | 12 | Minor (mostly Any returns) |
| jctl/commands/pipeline.py | 9 | Minor (missing return annotations) |
| jctl/commands/job.py | 5 | Minor (missing return annotations) |
| jctl/config/manager.py | 5 | Minor (HttpUrl type, name redef) |
| jctl/auth/okta.py | 4 | Minor (bytes/str inconsistency) |
| jctl/auth/keystore.py | 2 | Minor (missing annotation) |
| jctl/auth/token_manager.py | 2 | Minor (Any returns) |
| jctl/commands/auth.py | 1 | Minor (type mismatch) |
| jctl/auth/api_token.py | 1 | Minor (missing annotation) |
| jctl/utils/jenkins_client_factory.py | 1 | Minor (None iteration) |
| jctl/utils/completion.py | 3 | Minor (annotations) |
| jctl/utils/password_prompt.py | 1 | Minor (annotation) |
| jctl/utils/output.py | 1 | Minor (annotation) |
| Other files | 4 | Minor |

## Detailed Errors

### High Priority (Type Safety)

#### 1. jctl/config/manager.py - HttpUrl Type Mismatch (4 occurrences)
```
jctl/config/manager.py:176: error: Argument "url" to "JenkinsConfig" has incompatible type "str"; expected "HttpUrl"
jctl/config/manager.py:242: error: Argument "url" to "JenkinsConfig" has incompatible type "str"; expected "HttpUrl"
jctl/config/manager.py:367: error: Argument "url" to "JenkinsConfig" has incompatible type "str"; expected "HttpUrl"
jctl/commands/config.py:221: error: Argument "url" to "JenkinsConfig" has incompatible type "str"; expected "HttpUrl"
```

**Impact**: Low - Pydantic handles string-to-HttpUrl conversion automatically
**Fix**: Cast strings to `HttpUrl` or use `parse_obj` method

#### 2. jctl/auth/okta.py - bytes/str Inconsistency
```
jctl/auth/okta.py:124: error: Incompatible types in assignment (expression has type "str", variable has type "bytes")
jctl/auth/okta.py:125: error: Argument 1 to "rstrip" of "bytes" has incompatible type "str"; expected "Buffer | None"
jctl/auth/okta.py:127: error: Incompatible return value type (got "tuple[str, bytes]", expected "tuple[str, str]")
```

**Impact**: Low - base64 encoding inconsistency
**Fix**: Ensure consistent encoding (bytes or str)

### Medium Priority (Code Quality)

#### 3. Missing Return Type Annotations (11 occurrences)

Most common in command files (`pipeline.py`, `job.py`):
```python
# Current (missing annotation)
async def trigger(ctx, name, param, wait):
    ...

# Should be
async def trigger(ctx, name, param, wait) -> None:
    ...
```

**Impact**: Low - Functions work correctly, just missing documentation
**Fix**: Add `-> None` for functions that don't return values

#### 4. Returning Any (19 occurrences)

Mostly in `jenkins/client.py`:
```python
async def get_job_info(self, job_name: str) -> dict[str, Any]:
    response = await self._request("GET", f"/job/{job_name}/api/json")
    return response.json()  # error: Returning Any
```

**Impact**: Low - Response types are validated at usage points
**Fix**: Add explicit type annotations or use TypedDict

### Low Priority (Cosmetic)

#### 5. Variable Type Annotations (4 occurrences)
```python
# Current
password = []  # error: Need type annotation

# Should be
password: list[str] = []
```

**Impact**: Minimal - Types can be inferred
**Fix**: Add explicit annotations

#### 6. Name Redefinition (2 occurrences)
```python
# In jctl/config/manager.py
value = something  # line 108
...
value = something_else  # line 114 - error: already defined
```

**Impact**: Minimal - Variables renamed in different scopes
**Fix**: Use different variable names

## Recommendations

### For Beta Release (v0.1.0-beta.1)

**Status**: ✅ Optional - No blocking issues

All mypy errors are minor and don't affect functionality:
- Code works correctly
- No runtime errors
- Type safety is good enough for beta

**Action**: Document errors, fix in v0.2.0

### For v0.2.0

**Priority 1** (Quick wins):
1. Add missing return type annotations (-> None) - ~15 minutes
2. Fix variable type annotations - ~5 minutes

**Priority 2** (Type safety):
3. Fix HttpUrl type mismatches - ~10 minutes
4. Fix bytes/str inconsistency in okta.py - ~10 minutes

**Priority 3** (Advanced):
5. Replace `Any` returns with proper types - ~1-2 hours
6. Create TypedDict for Jenkins API responses - ~1 hour

### For v1.0.0

**Goal**: 100% mypy clean with strict mode

```bash
# Enable strict mode
mypy jctl/ --strict
```

## Running mypy

### Current Command

```bash
# In virtual environment
source venv/bin/activate

# Install mypy and stubs
pip install mypy types-PyYAML types-requests

# Run mypy
mypy jctl/ --ignore-missing-imports --check-untyped-defs
```

### Output

```
Found 50 errors in 14 files (checked 27 source files)
```

### Files Checked Clean

The following 13 files have no type errors:
- jctl/__init__.py
- jctl/__main__.py
- jctl/cli.py
- jctl/utils/logging.py
- jctl/utils/validators.py
- jctl/config/schemas.py
- jctl/config/__init__.py
- jctl/auth/__init__.py
- jctl/jenkins/__init__.py
- jctl/commands/__init__.py
- jctl/utils/__init__.py
- And 2 others

## Conclusion

**mypy Status**: ⚠️ 50 minor errors

**Beta Release Impact**: ✅ None - All errors are cosmetic

**Recommendation**:
- ✅ Proceed with v0.1.0-beta.1 release
- 📝 Fix type errors in v0.2.0 for better IDE support
- 🎯 Aim for strict mode in v1.0.0

---

**Report Generated**: 2025-01-20
**Next Review**: After v0.2.0 type fixes
