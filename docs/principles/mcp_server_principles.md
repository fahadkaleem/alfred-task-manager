# **ALFRED MCP SERVER INTEGRATION PRINCIPLES**

## **CORE PHILOSOPHY**
MCP integration is **TRANSPARENT PROTOCOL BRIDGING, not CUSTOM FRAMEWORK**. The server exposes tools cleanly, handles protocol details automatically, stays out of business logic.

## **THE GOLDEN RULES**

### **1. FASTMCP IS THE ONLY FRAMEWORK**
- All MCP server functionality through FastMCP
- No custom MCP protocol implementation
- No manual message handling or transport
- Let FastMCP handle protocol details automatically

### **2. TOOL DECORATORS ARE SACRED**
```python
Tool registration pattern (NEVER CHANGE):
@tool(name="tool_name", description="Clear description")
async def tool_handler(param: type) -> ToolResponse:
    return ToolResponse.success(data, message)
```

### **3. SERVER LIFECYCLE IS AUTOMATIC**
- Server startup/shutdown handled by FastMCP
- Lifespan context managers for initialization
- No manual server state management
- Transaction logging automatic on all tools

### **4. TOOL ISOLATION IS MANDATORY**
- Each tool is completely independent
- No shared state between tool calls
- No tool-to-tool communication
- Tools communicate only through state persistence

### **5. PROTOCOL ABSTRACTION IS COMPLETE**
- Business logic never sees MCP protocol details
- No raw MCP message handling in application code
- Tools work identically whether called via MCP or direct
- Protocol concerns isolated in server layer

### **6. ASYNC IS UNIVERSAL**
- All tool handlers are async functions
- Use `async/await` throughout the stack
- No blocking operations in tool handlers
- Concurrent tool execution supported

## **WHEN WORKING WITH MCP INTEGRATION**

### **DO:**
- ✅ Use `@tool` decorator for all exposed functions
- ✅ Return `ToolResponse` objects from all tools
- ✅ Keep tool handlers async and stateless
- ✅ Use FastMCP lifespan for initialization
- ✅ Let transaction logging happen automatically
- ✅ Validate inputs at tool entry points

### **DON'T:**
- ❌ Handle MCP protocol details manually
- ❌ Create custom MCP message handlers
- ❌ Share state between tool calls
- ❌ Block in async tool handlers
- ❌ Expose internal implementation via MCP
- ❌ Create tool interdependencies

## **SERVER SETUP PATTERNS**

### **Standard Server Configuration**
```python
# GOOD - Clean FastMCP setup
from fastmcp import FastMCP

app = FastMCP("Alfred Task Manager")

@app.lifespan
async def lifespan():
    """Initialization and cleanup"""
    # Initialize logging
    TransactionLogger.initialize()
    
    # Load configuration
    settings = load_settings()
    
    yield  # Server runs here
    
    # Cleanup if needed
    pass

# Tool registration happens via decorators
@app.tool(name="get_next_task")
async def get_next_task_handler() -> ToolResponse:
    # Business logic here
    pass

# BAD - Manual MCP handling
class CustomMCPServer:
    def handle_tool_call(self, message):  # NO! Let FastMCP handle this
        pass
```

### **Tool Registration Pattern**
```python
# GOOD - Standard tool pattern
@tool(
    name="implement_task",
    description="Execute implementation phase for a task that has completed planning"
)
async def implement_task_handler(task_id: str) -> ToolResponse:
    """
    Clear docstring explaining tool purpose and usage.
    
    Args:
        task_id: The unique identifier for the task
        
    Returns:
        ToolResponse with success/error and appropriate data
    """
    try:
        # Delegate to business logic
        handler = ToolFactory.get_handler("implement_task")
        return await handler.execute(task_id=task_id)
        
    except Exception as e:
        return ToolResponse.error(f"Failed to execute implement_task: {e}")

# BAD - Direct business logic in MCP handler
@tool(name="implement_task")
async def implement_task_handler(task_id: str) -> ToolResponse:
    # NO! Business logic belongs in handlers
    task = load_task(task_id)
    state_machine = create_state_machine()
    # ... complex logic here
```

## **TOOL PARAMETER PATTERNS**

### **Simple Parameters**
```python
@tool(name="get_task")
async def get_task_handler(task_id: str) -> ToolResponse:
    """Get a single task by ID"""
    if not task_id:
        return ToolResponse.error("Task ID is required")
    
    # Delegate to provider
    provider = ProviderFactory.create_provider()
    try:
        task = provider.get_task(task_id)
        return ToolResponse.success(task.model_dump(), f"Retrieved task {task_id}")
    except TaskNotFoundError:
        return ToolResponse.error(f"Task {task_id} not found")
```

### **Complex Parameters**
```python
@tool(name="submit_work")
async def submit_work_handler(task_id: str, artifact: dict) -> ToolResponse:
    """Submit work artifact for current workflow step"""
    if not task_id:
        return ToolResponse.error("Task ID is required")
    
    if not artifact:
        return ToolResponse.error("Artifact data is required")
    
    # Validate and delegate
    handler = ToolFactory.get_handler("submit_work")
    return await handler.execute(task_id=task_id, artifact=artifact)
```

## **ERROR HANDLING IN MCP CONTEXT**

### **Protocol Error Isolation**
```python
@tool(name="example_tool")
async def example_tool_handler(param: str) -> ToolResponse:
    """Always return ToolResponse - never let exceptions escape"""
    try:
        # Business logic
        result = perform_operation(param)
        return ToolResponse.success(result, "Operation completed")
        
    except ValidationError as e:
        # Map domain errors to user-friendly messages
        return ToolResponse.error(f"Invalid input: {e}")
        
    except Exception as e:
        # Catch all unexpected errors
        logger.exception(f"Unexpected error in {example_tool.__name__}")
        return ToolResponse.error(f"Internal error: {str(e)}")
```

### **No Protocol Details in Errors**
```python
# GOOD - User-friendly error
return ToolResponse.error("Task AL-123 not found. Check task ID and try again.")

# BAD - Protocol details exposed
return ToolResponse.error("MCP tool call failed: JSON-RPC error -32601")
```

## **TRANSACTION LOGGING INTEGRATION**

### **Automatic Logging Setup**
```python
# Transaction logging happens automatically via decorators
@tool(name="plan_task")
async def plan_task_handler(task_id: str) -> ToolResponse:
    # Logging happens automatically:
    # - Tool call logged on entry
    # - Parameters logged (sanitized)
    # - Response logged on exit
    # - Errors logged with stack traces
    
    handler = ToolFactory.get_handler("plan_task")
    return await handler.execute(task_id=task_id)
```

## **TESTING MCP INTEGRATION**

### **Test Tool Registration**
```python
def test_tool_registration():
    """Test that tools are properly registered with MCP server"""
    # Test tool is available
    assert "implement_task" in app.tools
    
    # Test tool metadata
    tool_info = app.tools["implement_task"]
    assert tool_info.name == "implement_task"
    assert "task_id" in tool_info.parameters
```

### **Test Tool Execution**
```python
@pytest.mark.asyncio
async def test_tool_execution():
    """Test tool execution returns proper ToolResponse"""
    # Test successful execution
    response = await implement_task_handler("AL-123")
    assert isinstance(response, ToolResponse)
    
    # Test error handling
    response = await implement_task_handler("")
    assert not response.success
    assert "required" in response.message.lower()
```

## **SERVER CONFIGURATION**

### **Standard Configuration**
```python
# main.py - Server entry point
if __name__ == "__main__":
    # FastMCP handles everything
    app.run(
        host=settings.server.host,
        port=settings.server.port,
        log_level=settings.log_level
    )
```

### **Development vs Production**
```python
# Development
app.run(debug=True, reload=True)

# Production  
app.run(
    host="0.0.0.0",
    port=8000,
    workers=1,  # MCP is single-threaded by design
    debug=False
)
```

## **PERFORMANCE CONSIDERATIONS**

### **Async Best Practices**
```python
# GOOD - Non-blocking operations
@tool(name="example_tool")
async def example_tool_handler(task_id: str) -> ToolResponse:
    # Use async file operations
    async with aiofiles.open(f"{task_id}.json") as f:
        content = await f.read()
    
    # Use async HTTP clients
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/api/tasks/{task_id}")
    
    return ToolResponse.success(content)

# BAD - Blocking operations
@tool(name="example_tool") 
async def example_tool_handler(task_id: str) -> ToolResponse:
    # Blocking file I/O
    with open(f"{task_id}.json") as f:  # Blocks event loop!
        content = f.read()
    
    # Blocking HTTP
    response = requests.get(f"/api/tasks/{task_id}")  # Blocks!
    
    return ToolResponse.success(content)
```

## **THE MCP SERVER PLEDGE**

*"I will not handle MCP protocol details manually. I will not create custom server logic. I will trust in FastMCP abstraction. When I think I need MCP customization, I will remember: The server is a tool transport, not business logic. Tools are independent, stateless functions. Protocol complexity belongs in the framework, not the application."*

## **ENFORCEMENT**

Any PR that:
- Implements custom MCP protocol handling → REJECTED
- Creates stateful tool handlers → REJECTED
- Adds manual transaction logging → REJECTED
- Exposes protocol details in business logic → REJECTED
- Creates tool interdependencies → REJECTED

MCP is transport. Tools are functions. FastMCP handles the rest.