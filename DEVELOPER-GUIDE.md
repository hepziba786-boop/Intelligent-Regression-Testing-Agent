# Developer Guide - SOAP Self-Healing Agent

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   SOAP Self-Healing Agent                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ SoapSelfHealingAgent (Orchestrator)                      │  │
│  │  - Controls iteration loop                              │  │
│  │  - Coordinates all components                           │  │
│  └────┬─────────────────────────────────────────────────┬──┘  │
│       │                                                 │      │
│   ┌───▼──────┐  ┌──────────────┐  ┌─────────────────┐ │      │
│   │ WSDL     │  │ SoapTest     │  │ SoapRequest    │ │      │
│   │ Analyzer │  │ Analyzer     │  │ Fixer          │ │      │
│   ├──────────┤  ├──────────────┤  ├────────────────┤ │      │
│   │ Parses   │  │ Runs tests   │  │ Generates      │ │      │
│   │ WSDL     │  │ Detects      │  │ fixed SOAP     │ │      │
│   │ Schema   │  │ failures     │  │ requests       │ │      │
│   │ Elements │  │ Extracts     │  │ Sample values  │ │      │
│   │ Types    │  │ requests     │  │ Updates        │ │      │
│   │ Required │  │ Updates      │  │ project        │ │      │
│   │ fields   │  │ project      │  │                │ │      │
│   └──────────┘  └──────────────┘  └────────────────┘ │      │
│       │                │                    │         │      │
│       └────────────────┼────────────────────┘         │      │
│                        │                              │      │
│                        └──────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
    Project Files
    - WSDL Schema
    - SoapUI Project
    - Test Results
    - Execution Logs
```

## Component Details

### 1. WSDLAnalyzer

**Purpose:** Parse and analyze WSDL files to extract service schema

**Key Methods:**

```python
class WSDLAnalyzer:
    def __init__(self, wsdl_path: str)
        # Parse WSDL and namespaces
    
    def get_request_schema(self, operation: str) -> Dict
        # Get schema for operation's request
        # Returns: Element with children representing required fields
    
    def get_required_fields(self, operation: str) -> List[str]
        # Get list of required field names
        # Returns: ['field1', 'field2', ...]
    
    def _parse_elements(self) -> Dict[str, Element]
        # Parse all XSD elements from schema
    
    def _parse_complex_type(self, complex_elem) -> List[Element]
        # Parse complex type children
```

**Data Model:**

```python
@dataclass
class Element:
    name: str                    # Field name
    type_name: str              # XSD type name
    element_type: ElementType   # Parsed type (STRING, BOOLEAN, etc.)
    min_occurs: int             # Minimum occurrences
    max_occurs: str             # Maximum occurrences
    is_required: bool           # Whether required
    children: List['Element']   # Child elements (for complex types)
```

### 2. SoapTestAnalyzer

**Purpose:** Execute tests and analyze results

**Key Methods:**

```python
class SoapTestAnalyzer:
    def run_tests(self, test_suite_name: Optional[str] = None) -> Dict
        # Execute tests via Maven
        # Returns: {returncode, stdout, stderr, passed}
    
    def extract_failures(self, test_output: str) -> List[Dict]
        # Parse test output for failures
        # Returns: List of failure dictionaries
    
    def get_test_requests(self) -> Dict[str, str]
        # Extract SOAP requests from project
        # Returns: {call_name: soap_xml}
    
    def update_request_in_project(self, call_name: str, new_request: str) -> bool
        # Update a specific request in project
        # Returns: bool (success/failure)
    
    def save_project(self)
        # Write updated project to disk
```

### 3. SoapRequestFixer

**Purpose:** Generate and fix SOAP requests based on schema

**Key Methods:**

```python
class SoapRequestFixer:
    @staticmethod
    def parse_soap_request(soap_xml: str) -> Dict
        # Parse SOAP XML structure
        # Returns: {raw, root, namespaces}
    
    @staticmethod
    def generate_sample_value(element: Element) -> str
        # Generate type-appropriate sample value
        # Returns: "true", "2024-08-13", "SampleValue", etc.
    
    @staticmethod
    def fix_request_from_wsdl(
        soap_request: str, 
        wsdl_schema: Element,
        operation_name: str
    ) -> str
        # Generate fixed SOAP request
        # Returns: Updated SOAP XML
```

**Sample Value Generation:**

```python
ElementType.BOOLEAN   → "true"
ElementType.STRING    → "SampleValue"
ElementType.INTEGER   → "123"
ElementType.DECIMAL   → "123.45"
ElementType.DATE      → "2024-08-13"
ElementType.DATETIME  → "2024-08-13T10:30:00"
```

### 4. SoapSelfHealingAgent

**Purpose:** Orchestrate the entire process

**Main Loop:**

```python
def run(self) -> bool:
    while iteration < max_iterations:
        # 1. Run tests
        test_result = self.test_analyzer.run_tests()
        
        # 2. Check if passed
        if test_result['passed']:
            return True  # Success!
        
        # 3. Analyze failures
        failures = self.test_analyzer.extract_failures(output)
        
        # 4. Get requests to fix
        requests = self.test_analyzer.get_test_requests()
        
        # 5. Fix each request
        for call_name, request_xml in requests.items():
            operation = self._extract_operation_from_request(request_xml)
            schema = self.wsdl_analyzer.get_request_schema(operation)
            fixed = self.request_fixer.fix_request_from_wsdl(
                request_xml, schema, operation
            )
            
            self.test_analyzer.update_request_in_project(call_name, fixed)
        
        # 6. Save and continue
        self.test_analyzer.save_project()
        time.sleep(retry_delay)
```

## Extending the Agent

### Custom WSDL Analyzer

```python
class MyCustomWSDLAnalyzer(WSDLAnalyzer):
    def _parse_elements(self) -> Dict[str, Element]:
        # Add custom parsing logic
        elements = super()._parse_elements()
        
        # Custom processing
        for name, elem in elements.items():
            if self._is_deprecated(name):
                elements.pop(name)
        
        return elements
    
    def _is_deprecated(self, element_name: str) -> bool:
        # Check for deprecated elements
        deprecated = ['oldField1', 'oldField2']
        return element_name in deprecated
```

### Custom Request Fixer

```python
class MyCustomRequestFixer(SoapRequestFixer):
    @staticmethod
    def generate_sample_value(element: Element) -> str:
        # Custom sample value generation
        
        if element.name == "applicantName":
            return "John Doe"
        elif element.name == "caseId":
            return "CASE-" + datetime.now().strftime("%Y%m%d%H%M%S")
        elif element.name == "phoneNumber":
            return "+1-555-0123"
        
        # Fall back to parent
        return super().generate_sample_value(element)
```

### Custom Test Analyzer

```python
class MyCustomTestAnalyzer(SoapTestAnalyzer):
    def run_tests(self, test_suite_name: Optional[str] = None) -> Dict:
        # Custom test execution logic
        
        if self._is_local_test():
            # Run local tests faster
            return self._run_local_tests()
        else:
            # Run remote tests
            return super().run_tests(test_suite_name)
    
    def _is_local_test(self) -> bool:
        return os.getenv('TEST_ENV') == 'local'
    
    def _run_local_tests(self) -> Dict:
        # Custom implementation
        pass
```

## Extension Points

### 1. Custom Failure Detection

Override `extract_failures()` to detect custom failure patterns:

```python
def extract_failures(self, test_output: str) -> List[Dict]:
    failures = super().extract_failures(test_output)
    
    # Add custom detection
    custom_patterns = [
        r'CustomError: (.+?)(?:\n|$)',
        r'BusinessLogicFault: (.+?)(?:\n|$)',
    ]
    
    for pattern in custom_patterns:
        matches = re.finditer(pattern, test_output)
        for match in matches:
            failures.append({
                'message': match.group(1),
                'type': 'custom',
                'pattern': pattern
            })
    
    return failures
```

### 2. Custom Sample Value Generation

```python
class DomainSpecificFixer(SoapRequestFixer):
    PHONE_NUMBERS = ["555-0100", "555-0101", "555-0102"]
    CASE_TYPES = ["CIVIL", "CRIMINAL", "FAMILY"]
    
    @staticmethod
    def generate_sample_value(element: Element) -> str:
        if element.name == "phoneNumber":
            return random.choice(DomainSpecificFixer.PHONE_NUMBERS)
        elif element.name == "caseType":
            return random.choice(DomainSpecificFixer.CASE_TYPES)
        
        return SoapRequestFixer.generate_sample_value(element)
```

### 3. Pre/Post Processing Hooks

```python
class HookedAgent(SoapSelfHealingAgent):
    def run(self) -> bool:
        self._pre_run_hook()
        
        result = super().run()
        
        self._post_run_hook(result)
        
        return result
    
    def _pre_run_hook(self):
        # Setup, create reports, etc.
        print("[*] Agent starting...")
    
    def _post_run_hook(self, success: bool):
        # Cleanup, send notifications, etc.
        if success:
            self._send_success_notification()
        else:
            self._send_failure_notification()
    
    def _send_success_notification(self):
        # Send email, Slack message, etc.
        pass
```

## Testing the Agent

### Unit Tests

```python
import unittest
from soap_self_healing_agent import Element, ElementType, SoapRequestFixer

class TestSoapRequestFixer(unittest.TestCase):
    def test_generate_boolean_value(self):
        elem = Element(
            name="active",
            type_name="boolean",
            element_type=ElementType.BOOLEAN
        )
        value = SoapRequestFixer.generate_sample_value(elem)
        self.assertIn(value, ["true", "false"])
    
    def test_generate_date_value(self):
        elem = Element(
            name="birthDate",
            type_name="date",
            element_type=ElementType.DATE
        )
        value = SoapRequestFixer.generate_sample_value(elem)
        # Should be YYYY-MM-DD format
        self.assertRegex(value, r'\d{4}-\d{2}-\d{2}')

if __name__ == '__main__':
    unittest.main()
```

### Integration Tests

```python
def test_full_workflow():
    # Create temp WSDL
    wsdl_content = """<?xml version="1.0"?>
    <wsdl:definitions ...>
        ...WSDL content...
    </wsdl:definitions>"""
    
    # Create temp project
    project_content = """<?xml version="1.0"?>
    <con:soapui-project ...>
        ...project content...
    </con:soapui-project>"""
    
    # Initialize agent
    agent = SoapSelfHealingAgent(
        "/tmp/test_project",
        "/tmp/test.wsdl",
        "/tmp/test-project.xml"
    )
    
    # Run agent
    result = agent.run()
    
    # Assert success
    assert result == True
```

## Debugging

### Enable Detailed Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Agent starting...")
logger.info("Test iteration 1...")
logger.warning("Failure detected")
logger.error("Critical error")
```

### Inspect Data Structures

```python
# Debug WSDL parsing
import json
from soap_self_healing_agent import WSDLAnalyzer

wsdl = WSDLAnalyzer('service.wsdl')

# Print service info
print(f"Service: {wsdl.service_name}")
print(f"Operations: {list(wsdl.operations.keys())}")

# Print schema for operation
schema = wsdl.get_request_schema('createCaseFile')
print(json.dumps(schema.__dict__, indent=2, default=str))

# Print required fields
required = wsdl.get_required_fields('createCaseFile')
print(f"Required fields: {required}")
```

### Step-by-Step Execution

```python
# Run agent with manual steps
from soap_self_healing_agent import (
    WSDLAnalyzer, 
    SoapTestAnalyzer, 
    SoapRequestFixer,
    SoapSelfHealingAgent
)

wsdl = WSDLAnalyzer('service.wsdl')
analyzer = SoapTestAnalyzer('project.xml')
fixer = SoapRequestFixer()

# Step 1: Analyze WSDL
print("Step 1: Analyzing WSDL...")
schema = wsdl.get_request_schema('createCaseFile')
print(f"  Schema: {schema}")

# Step 2: Get test requests
print("\nStep 2: Getting test requests...")
requests = analyzer.get_test_requests()
for name, xml in requests.items():
    print(f"  {name}: {len(xml)} chars")

# Step 3: Fix request
print("\nStep 3: Fixing requests...")
for name, xml in requests.items():
    fixed = fixer.fix_request_from_wsdl(xml, schema, 'createCaseFile')
    print(f"  Fixed {name}")

# Step 4: Save
print("\nStep 4: Saving project...")
analyzer.save_project()
print("  Saved!")
```

## Performance Optimization

### Caching WSDL Analysis

```python
import hashlib

class CachedWSDLAnalyzer(WSDLAnalyzer):
    CACHE = {}
    
    def __init__(self, wsdl_path: str):
        self.wsdl_hash = self._hash_file(wsdl_path)
        
        if self.wsdl_hash in self.CACHE:
            # Reuse cached analysis
            cached = self.CACHE[self.wsdl_hash]
            self.namespaces = cached['namespaces']
            self.service_name = cached['service_name']
            self.operations = cached['operations']
            self.elements = cached['elements']
        else:
            # Perform analysis and cache
            super().__init__(wsdl_path)
            self.CACHE[self.wsdl_hash] = {
                'namespaces': self.namespaces,
                'service_name': self.service_name,
                'operations': self.operations,
                'elements': self.elements
            }
    
    @staticmethod
    def _hash_file(filepath: str) -> str:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
```

### Parallel Test Execution

```python
from concurrent.futures import ThreadPoolExecutor

def run_tests_parallel(agent_instances: List[SoapSelfHealingAgent]):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(lambda agent: agent.run(), agent_instances)
    return list(results)
```

## Best Practices

1. **Error Handling**: Always wrap external calls in try-except
2. **Logging**: Use logging module, not print()
3. **Type Hints**: Add type annotations to all methods
4. **Docstrings**: Document all classes and methods
5. **Testing**: Write tests for custom extensions
6. **Config**: Use configuration files, not hardcoded values
7. **Versioning**: Track changes in version numbers
8. **Documentation**: Keep docs updated with code changes

## Code Style

```python
# Good: Clear variable names, type hints, docstring
def fix_request_from_wsdl(
    soap_request: str, 
    wsdl_schema: Element,
    operation_name: str
) -> str:
    """
    Generate corrected SOAP request based on WSDL schema.
    
    Args:
        soap_request: Original SOAP request XML
        wsdl_schema: Element with schema definition
        operation_name: Name of the SOAP operation
    
    Returns:
        Fixed SOAP request XML with all required fields
    """
    # Implementation
    pass

# Bad: Unclear names, no hints, no docs
def fix(r, s, o):
    # Fix request
    pass
```

## Performance Metrics

Add instrumentation to track performance:

```python
import time
from functools import wraps

def timed_operation(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"[PERF] {func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper

class InstrumentedAgent(SoapSelfHealingAgent):
    @timed_operation
    def run(self):
        return super().run()
```

## Contributing

To contribute:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Follow code style guidelines
5. Submit pull request
6. Request review from maintainers

## References

- WSDL Specification: https://www.w3.org/TR/wsdl
- SOAP Protocol: https://www.w3.org/TR/soap12/
- XML Schema: https://www.w3.org/XML/Schema
- SoapUI Documentation: https://www.soapui.org/
- Python XML: https://docs.python.org/3/library/xml.etree.elementtree.html

---

**Last Updated:** 2024-08-13  
**Maintainer:** Development Team
