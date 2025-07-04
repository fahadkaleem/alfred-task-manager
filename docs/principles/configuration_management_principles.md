# **ALFRED CONFIGURATION MANAGEMENT PRINCIPLES**

## **CORE PHILOSOPHY**
Configuration is **IMMUTABLE DATA, not RUNTIME VARIABLES**. Set once, trust forever. Changes require restarts.

## **THE GOLDEN RULES**

### **1. THREE-TIER HIERARCHY IS SACRED**
- **Tier 1**: Package defaults (built-in fallbacks)
- **Tier 2**: Global `settings` (environment-driven, immutable)
- **Tier 3**: Project `alfred.yml` (mutable, project-specific)
- This hierarchy is FROZEN. Do not add more tiers.

### **2. IMMUTABILITY ABOVE ALL**
- Global `settings` are loaded ONCE at startup
- No runtime modification of global configuration
- Project configs can change, but require explicit save operations
- Environment variables override everything (deployment-time decisions)

### **3. VALIDATION IS NON-NEGOTIABLE**
```python
Configuration validation requirements:
- All configs MUST use Pydantic models
- Invalid configs MUST fail fast at startup
- No silent fallbacks or default substitutions
- Provide actionable error messages with examples
```

### **4. ENVIRONMENT VARIABLES ARE SACRED**
```bash
Standard environment variable format:
ALFRED_DEBUG=true
ALFRED_LOG_LEVEL=debug
ALFRED_PROVIDER=jira
```
- All env vars use `ALFRED_` prefix
- Boolean values: `true/false` (lowercase)
- No env var can be overridden by file config

### **5. ATOMIC OPERATIONS ONLY**
- All config writes use temporary files + atomic move
- No partial config updates
- File locks prevent concurrent modifications
- Failed writes leave original config intact

### **6. FEATURE FLAGS ARE SIMPLE BOOLEANS**
```python
# GOOD - Simple boolean flags
feature_flags:
  enable_new_parser: true
  use_advanced_scoring: false

# BAD - Complex feature configuration
feature_flags:
  parser:
    version: "v2"
    settings: {...}
```

## **WHEN WORKING WITH CONFIGURATION**

### **DO:**
- ✅ Use Pydantic models for all config structures
- ✅ Validate configuration at startup
- ✅ Use atomic file operations for saves
- ✅ Provide clear error messages for invalid configs
- ✅ Document all configuration options in models
- ✅ Use environment variables for deployment settings

### **DON'T:**
- ❌ Modify global settings at runtime
- ❌ Add configuration caching or reloading
- ❌ Create dynamic configuration generation
- ❌ Use configuration for runtime state
- ❌ Add conditional configuration logic
- ❌ Create configuration inheritance chains

## **CONFIGURATION CATEGORIES**

### **Global Settings (Immutable)**
- Server configuration (ports, hosts)
- Logging levels and debug flags
- Provider selection and authentication
- Feature flags for system behavior

### **Project Configuration (Mutable)**
- Workflow customizations
- Project-specific provider settings
- Task templates and formats
- Local development overrides

### **"But I need runtime configuration!"**
No, you need runtime STATE. Use the state management system instead.

## **CONFIGURATION EXAMPLES**

### **GOOD Example - Proper structure:**
```python
class AlfredConfig(BaseModel):
    version: str = "1.0"
    providers: ProvidersConfig
    workflows: WorkflowConfig
    features: FeatureFlags
    
    @validator('version')
    def validate_version(cls, v):
        if v not in SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported version: {v}")
        return v
```

### **BAD Example - Runtime modification:**
```python
# NEVER DO THIS
def update_provider(new_provider):
    config.providers.default = new_provider  # NO!
    config.save()  # This breaks immutability!
```

## **TESTING CONFIGURATION**

Test configuration loading, not configuration content:

```python
def test_config_validation():
    # Test validation works
    with pytest.raises(ValidationError):
        AlfredConfig(version="invalid")
    
    # Test environment override
    with mock.patch.dict(os.environ, {"ALFRED_DEBUG": "true"}):
        config = load_config()
        assert config.debug is True
```

## **THE CONFIGURATION PLEDGE**

*"I will not modify configuration at runtime. I will not add configuration complexity. I will trust in immutability. When I think I need dynamic configuration, I will remember: I need dynamic STATE, not dynamic CONFIG. Configuration is for deployment decisions, not runtime decisions."*

## **ENFORCEMENT**

Any PR that:
- Modifies global settings at runtime → REJECTED
- Adds configuration reloading → REJECTED
- Creates dynamic config generation → REJECTED
- Bypasses validation → REJECTED
- Adds more than 3 tiers → REJECTED

Configuration is for deployment decisions. State is for runtime decisions. Do not confuse them.