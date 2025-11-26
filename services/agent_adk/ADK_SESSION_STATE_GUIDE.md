# ADK Session State Guide

## Overview
The session state in Google's Agent Development Kit (ADK) is a crucial mechanism for maintaining context and passing data between the frontend application and agent tools throughout a conversation.

## How Session State Works

### 1. State Initialization
When creating a new session, you must pass the initial state as a property in the request body:

```javascript
// Frontend (adk-agent.ts)
const response = await fetch(
  `${API_BASE_URL}/apps/${APP_NAME}/users/${userId}/sessions`,
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${authToken}`
    },
    body: JSON.stringify({ 
      state: {
        // Your initial state data here
        user_id: userId,
        auth_token: authToken,
        // ... other properties
      }
    }),
  }
);
```

**Important:** The state must be sent as a property `{ state: {...} }`, NOT directly as the body.

### 2. State Structure
The state should be a flat key-value structure with serializable values:

```javascript
const state = {
  // User authentication
  user_id: "uuid-here",
  auth_token: "jwt-token-here",
  authenticated: true,
  
  // User profile data
  user_name: "John Doe",
  user_email: "john@example.com",
  user_role: "business",
  business_name: "Acme Corp",
  
  // Application-specific data
  tenant_id: "tenant-uuid",
  // ... other properties as needed
};
```

### 3. Accessing State in Agent Tools

In your agent tools (Python), the state is available through the `tool_context` parameter:

```python
from google.adk.tools.tool_context import ToolContext

def my_tool_function(param1: str, tool_context: ToolContext = None) -> dict:
    """Tool function that needs access to session state."""
    
    if tool_context and hasattr(tool_context, 'state'):
        # Access state as object attributes
        if hasattr(tool_context.state, 'auth_token'):
            auth_token = tool_context.state.auth_token
            # Use the auth token for API calls
        
        if hasattr(tool_context.state, 'user_id'):
            user_id = tool_context.state.user_id
            # Use the user_id as needed
    
    # Tool logic here
    return {"status": "success"}
```

### 4. State Prefixes and Scopes

ADK supports different state scopes using prefixes:

- **No prefix** (Session State): Specific to the current session
  - Example: `auth_token`, `current_task`
  
- **`user:` prefix**: Tied to the user, shared across all their sessions
  - Example: `user:preferences`, `user:settings`
  
- **`app:` prefix**: Shared across all users in the application
  - Example: `app:version`, `app:feature_flags`
  
- **`temp:` prefix**: Temporary, discarded after processing
  - Example: `temp:processing_flag`, `temp:debug_info`

### 5. Updating State During Conversation

State can be updated through events:

```python
from google.adk.events.event import Event

# In your agent code
yield Event(
    author=self.name,
    actions={
        "state_delta": {
            "task_completed": True,
            "last_action": "created_product"
        }
    }
)
```

## Best Practices

### ✅ DO:
1. **Keep state flat**: Use a shallow structure for better performance
2. **Use clear keys**: Descriptive names like `auth_token` instead of `token`
3. **Store only essential data**: Don't store large objects or unnecessary data
4. **Use appropriate prefixes**: Choose the right scope for your data
5. **Validate state existence**: Always check if state and properties exist before accessing

### ❌ DON'T:
1. **Don't modify state directly**: Always use events or proper update methods
2. **Don't store sensitive data unnecessarily**: Only keep auth tokens when needed
3. **Don't use deeply nested structures**: Keep the state flat and simple
4. **Don't assume state exists**: Always check with `hasattr()` before accessing

## Common Use Cases

### Authentication Flow
```javascript
// Frontend: Pass auth token in initial state
const state = {
  user_id: userId,
  auth_token: jwtToken,
  authenticated: true
};

// Agent Tool: Use auth token for API calls
if hasattr(tool_context.state, 'auth_token'):
    headers = {
        "Authorization": f"Bearer {tool_context.state.auth_token}"
    }
    response = requests.get(api_url, headers=headers)
```

### Multi-tenant Support
```javascript
// Frontend: Include tenant information
const state = {
  user_id: userId,
  tenant_id: selectedTenantId,
  tenant_name: tenantName
};

// Agent Tool: Use tenant context
if hasattr(tool_context.state, 'tenant_id'):
    tenant_id = tool_context.state.tenant_id
    # Query tenant-specific data
```

## Debugging Tips

1. **Add logging in tools** to see what's in the state:
```python
if tool_context and hasattr(tool_context, 'state'):
    print(f"State type: {type(tool_context.state)}")
    print(f"State attributes: {dir(tool_context.state)}")
```

2. **Check FastAPI endpoint** to ensure state is being received:
```python
# In fast_api.py
async def create_session(
    app_name: str,
    user_id: str,
    state: Optional[dict[str, Any]] = None,
    ...
):
    logger.info(f"Creating session with state: {state}")
```

3. **Verify frontend is sending state correctly**:
```javascript
console.log("Sending state:", { state: stateObject });
```

## Example: Complete Authentication Flow

### 1. Frontend (adk-agent.ts)
```typescript
export async function createSession(
  userId: string, 
  userProfile?: UserProfile, 
  authToken?: string
): Promise<ApiSession> {
  const state = {
    user_id: userId,
    user_name: userProfile?.fullName,
    user_email: userProfile?.email,
    user_role: userProfile?.role,
    business_name: userProfile?.businessName,
    auth_token: authToken,
    authenticated: !!authToken
  };

  const response = await fetch(
    `${API_BASE_URL}/apps/${APP_NAME}/users/${userId}/sessions`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${authToken}`
      },
      body: JSON.stringify({ state }), // ✅ Correct format
    }
  );
  
  return await response.json();
}
```

### 2. Agent Tool (tools.py)
```python
def execute_api_call(
    endpoint: str,
    tool_context: ToolContext = None
) -> dict:
    """Execute API call with authentication from session state."""
    
    # Get auth token from session state
    auth_token = None
    if tool_context and hasattr(tool_context, 'state'):
        if hasattr(tool_context.state, 'auth_token'):
            auth_token = tool_context.state.auth_token
    
    if not auth_token:
        return {
            "status": "error",
            "message": "No authentication token in session"
        }
    
    # Use the token for API call
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(endpoint, headers=headers)
    
    return {
        "status": "success",
        "data": response.json()
    }
```

## Troubleshooting

### Issue: State not arriving in tools
**Solution:** Ensure you're sending state as `{ state: {...} }` not just `{...}`

### Issue: Can't access state properties
**Solution:** Use `hasattr()` to check if properties exist, as state is an object not a dict

### Issue: State lost between messages
**Solution:** State persists per session. Ensure you're using the same session_id

### Issue: Authentication failing
**Solution:** Verify the auth_token is being passed in initial state and accessed correctly in tools