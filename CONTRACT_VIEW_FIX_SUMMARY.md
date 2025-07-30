# Contract View API Field Name Fix

## Problem
The `contract_view` API was returning validation errors because:

1. **Missing required field**: The API expected `contractId` (camelCase) but was receiving `contract_id` (snake_case)
2. **Extra forbidden field**: The API was rejecting `contract_id` as an extra field that wasn't allowed

## Error Details
```
{"detail":[{"type":"missing","loc":["body","contractId"],"msg":"Field required","input":{"reviewStage":"初审","reviewList":5,"reviewRules":[...],"contract_id":"8888"}},{"type":"extra_forbidden","loc":["body","contract_id"],"msg":"Extra inputs are not permitted","input":"8888"}]}
```

## Root Cause
In `ContractAudit/main.py`, the `default_contract_view_fields` was using `"contract_id": "8888"` instead of `"contractId": "8888"`.

## Fixes Applied

### 1. Fixed Default Field Name
**File**: `ContractAudit/main.py` (line ~726)
```python
# Before
"contract_id": "8888",

# After  
"contractId": "8888",
```

### 2. Enhanced Field Mapping Logic
**File**: `ContractAudit/main.py` (lines ~730-755)
Added special handling for the `contractId` field to ensure it's properly mapped from various sources:

```python
# Special handling for contractId field
if "contractId" in contract_view_payload:
    # Ensure contractId field exists and is correct
    contract_id_value = (
        message_data.get("contractId") or 
        message_data.get("contract_id") or 
        contract_view_payload["contractId"]
    )
    contract_view_payload["contractId"] = contract_id_value
else:
    # If no contractId, get from message_data
    contract_id_value = (
        message_data.get("contractId") or 
        message_data.get("contract_id") or 
        "8888"
    )
    contract_view_payload["contractId"] = contract_id_value
```

### 3. Updated Response Field Handling
**File**: `ContractAudit/main.py` (line ~911)
Updated to handle both camelCase and snake_case field names in the response:

```python
# Before
contract_id = contract_view_result.get("contract_id") or message_data.get("contract_id")

# After
contract_id = contract_view_result.get("contractId") or contract_view_result.get("contract_id") or message_data.get("contract_id")
```

### 4. Updated Rule Processing
**File**: `ContractAudit/main.py` (lines ~1016-1022)
Updated the rule processing to handle both field name formats:

```python
completed_rule['contract_id'] = get_first(
    matched_rule.get('contractId') or matched_rule.get('contract_id'),
    fr.get('contractId'), fr.get('contract_id'),
    message_data.get('contract_id'),
    contract_view_result.get('contractId') or contract_view_result.get('contract_id'),
    "8888"
)
```

## Testing
Created `test_contract_view_fix.py` to verify the fix works correctly.

## Result
The `contract_view` API should now work correctly with the proper camelCase field names, eliminating the validation errors and allowing the contract review process to proceed normally. 