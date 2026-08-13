# SOAP Self-Healing Test Agent

## Overview

The **SOAP Self-Healing Test Agent** is an intelligent automation framework that runs SOAP web service tests and automatically fixes failures by analyzing the WSDL schema. It provides a self-correcting testing mechanism that can adapt to service changes without manual intervention.

### Key Features

✅ **Automatic WSDL Analysis** - Parses WSDL files to understand service schema and data type requirements
✅ **Intelligent Failure Detection** - Identifies assertion failures and SOAP faults  
✅ **Auto-Fix Capability** - Automatically generates correct SOAP requests based on WSDL schema
✅ **Iterative Healing** - Re-runs tests after each fix with configurable retry limits
✅ **Field Validation** - Ensures all required fields are present and correct types
✅ **Request Regeneration** - Generates appropriate sample values based on field types (boolean, string, date, etc.)
✅ **Project Updates** - Saves fixed requests back to SoapUI project file
✅ **Detailed Logging** - Tracks all iterations and failures for debugging

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. RUN TESTS                                               │
│     Execute SOAP tests from SoapUI project                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. CHECK RESULTS                                           │
│     All tests passed? ──NO──┐                              │
│     ▲                        │                              │
│     │                        ▼                              │
│     └──────YES──► END ◄─ Extract failures                 │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. ANALYZE WSDL                                            │
│     Parse schema for required fields                       │
│     Extract data type requirements                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. FIX REQUESTS                                            │
│     Add missing required fields                            │
│     Generate appropriate sample values                     │
│     Update SoapUI project                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ (Return to Step 1)
```

## Installation

### Prerequisites
- Python 3.7+
- Maven 3.6+
- Java 8+
- SoapUI project file (XML format)
- WSDL file

### Setup

```bash
# Navigate to project directory
cd /path/to/Intelligent-Regression-Testing-Agent

# Install Python dependencies (optional, most are built-in)
pip3 install -r requirements.txt

# Make the runner script executable
chmod +x run-agent.sh
```

## Usage

### Quick Start

```bash
# Using the shell script (recommended)
./run-agent.sh

# Or run directly with Python
python3 soap-self-healing-agent.py
```

### Expected Output

```
======================================================================
INTELLIGENT SOAP SELF-HEALING TEST AGENT
======================================================================
Service: CaseFileService
WSDL: /path/to/CaseFileService-v3-priorityMandatory.wsdl
Project: /path/to/Intelligent-Regression-Testing-Agent-final.xml
======================================================================

[ITERATION 1/5]
----------------------------------------------------------------------
[*] Running SOAP tests from /path/to/project...
[*] Analyzing test failures...
  Failure 1: Missing required element 'priorityFlag'
  
[*] Analyzing WSDL and fixing requests...
  Processing: createCaseFile
    [+] Added required field 'priorityFlag' = 'true'
    [+] Updated request 'createCaseFile'
[+] Project saved: /path/to/Intelligent-Regression-Testing-Agent-final.xml

[ITERATION 2/5]
----------------------------------------------------------------------
[✓] ALL TESTS PASSED!

======================================================================
SUCCESS! All tests passed on iteration 2
======================================================================
```

## Configuration

### agent-config.json

The agent reads configuration from `agent-config.json`:

```json
{
  "execution": {
    "max_iterations": 5,      // Maximum retry attempts
    "retry_delay": 2,         // Seconds between retries
    "timeout": 60             // Test execution timeout
  },
  "request_fixing": {
    "auto_fix_missing_required_fields": true,
    "generate_sample_values": true,
    "preserve_existing_values": true
  }
}
```

## Architecture

### Main Components

#### WSDLAnalyzer
Parses WSDL files and extracts:
- Service definitions
- Operation schemas  
- Element definitions with type information
- Required vs optional fields

```python
wsdl = WSDLAnalyzer('service.wsdl')
schema = wsdl.get_request_schema('operationName')
required_fields = wsdl.get_required_fields('operationName')
```

#### SoapTestAnalyzer
Manages SoapUI project interaction:
- Executes tests via Maven
- Extracts test requests
- Parses test output for failures
- Updates project files

```python
analyzer = SoapTestAnalyzer('project.xml')
result = analyzer.run_tests()
requests = analyzer.get_test_requests()
analyzer.update_request_in_project('callName', newXML)
```

#### SoapRequestFixer
Generates and fixes SOAP requests:
- Parses existing requests
- Generates type-appropriate sample values
- Adds missing required fields
- Formats SOAP XML

```python
fixer = SoapRequestFixer()
fixed = fixer.fix_request_from_wsdl(request, schema, operation)
```

#### SoapSelfHealingAgent
Orchestrates the entire process:
- Runs iteration loop
- Coordinates WSDL analysis with test execution
- Manages failures and retries
- Logs execution history

## Supported Field Types

The agent can automatically generate appropriate values for:

| Field Type | Sample Value | Example |
|-----------|--------------|---------|
| String | `SampleValue` | Text, IDs, names |
| Boolean | `true` | Flags, switches |
| Integer | `123` | Counts, amounts |
| Decimal | `123.45` | Prices, ratios |
| Date | `2024-08-13` | Birth dates, deadlines |
| DateTime | `2024-08-13T10:30:00` | Timestamps |

## Example: Handling WSDL Schema Changes

### Original WSDL (v1)
```xml
<xsd:element name="createCaseFileRequest">
  <xsd:complexType>
    <xsd:sequence>
      <xsd:element name="caseId" type="xsd:string"/>
      <xsd:element name="applicantName" type="xsd:string"/>
    </xsd:sequence>
  </xsd:complexType>
</xsd:element>
```

### Updated WSDL (v3)
```xml
<xsd:element name="createCaseFileRequest">
  <xsd:complexType>
    <xsd:sequence>
      <xsd:element name="caseId" type="xsd:string"/>
      <xsd:element name="applicantName" type="xsd:string"/>
      <xsd:element name="priorityFlag" type="xsd:boolean"/>  <!-- NEW REQUIRED FIELD -->
    </xsd:sequence>
  </xsd:complexType>
</xsd:element>
```

### Agent Behavior

When tests fail with the updated WSDL:
1. Agent detects missing `priorityFlag` field
2. Analyzes WSDL schema to find it's required
3. Determines it's a boolean type
4. Generates sample value `true`
5. Updates SOAP request to include: `<priorityFlag>true</priorityFlag>`
6. Re-runs tests
7. Tests pass! ✓

## Integration with CI/CD

### GitHub Actions

```yaml
name: SOAP Tests with Self-Healing
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-java@v2
        with:
          java-version: '11'
      - run: |
          python3 -m pip install -r requirements.txt
          chmod +x run-agent.sh
          ./run-agent.sh
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('SOAP Self-Healing Tests') {
            steps {
                sh 'chmod +x run-agent.sh'
                sh './run-agent.sh'
            }
        }
    }
    post {
        always {
            archive 'agent-execution.log'
        }
    }
}
```

## Troubleshooting

### Issue: "No WSDL file found"
**Solution**: Ensure your WSDL file is in the project root directory

```bash
ls -la *.wsdl
```

### Issue: "No SoapUI project file found"
**Solution**: SoapUI project must be an XML file with "final" in the name

```bash
ls -la *final.xml
```

### Issue: Tests timeout
**Solution**: Increase timeout in `agent-config.json`

```json
{
  "execution": {
    "timeout": 120
  }
}
```

### Issue: Agent stops without fixing
**Solution**: Check if:
- WSDL file is valid XML
- SoapUI project contains test cases
- Maven can execute tests independently

```bash
# Test Maven execution directly
mvn test -DtestSuite="TestSuite 1"
```

## Advanced Usage

### Custom Sample Values

Modify `SoapRequestFixer.generate_sample_value()` to customize sample value generation:

```python
@staticmethod
def generate_sample_value(element: Element) -> str:
    if element.name == "applicantName":
        return "John Doe"
    elif element.name == "caseId":
        return "CASE-2024-001"
    # ... default behavior
```

### Extending the Agent

Create custom analyzers by subclassing:

```python
class CustomWSDLAnalyzer(WSDLAnalyzer):
    def custom_validation(self):
        # Add custom WSDL validation logic
        pass

class CustomSoapRequestFixer(SoapRequestFixer):
    @staticmethod
    def generate_sample_value(element: Element) -> str:
        # Custom sample value generation
        pass
```

## Logs and Debugging

Agent execution logs are saved to `agent-execution.log`:

```
[2024-08-13 10:30:45] INFO: Starting SOAP Self-Healing Agent
[2024-08-13 10:30:46] INFO: WSDL Analysis Complete
[2024-08-13 10:30:47] INFO: Test Iteration 1 - Running tests...
[2024-08-13 10:30:52] ERROR: Assertion failure detected
[2024-08-13 10:30:53] INFO: Fixing request: priorityFlag
[2024-08-13 10:30:54] INFO: Project saved
[2024-08-13 10:30:55] INFO: Test Iteration 2 - Running tests...
[2024-08-13 10:31:00] INFO: All tests passed!
```

Enable verbose debug mode (future enhancement):

```bash
python3 soap-self-healing-agent.py --debug
```

## Performance Metrics

Typical execution times:
- WSDL Analysis: 100-200ms
- Single test run: 5-15 seconds
- Request fixing: 50-100ms per request
- Full iteration: 5-20 seconds

## Limitations and Future Enhancements

### Current Limitations
- Supports SOAP 1.1 over HTTP
- Requires Maven for test execution
- Limited to XSD schema validation

### Planned Features
- SOAP 1.2 support
- WSDL 2.0 support
- Gradle/Ant build system support
- Machine learning-based failure prediction
- Automated test case generation
- REST API endpoint support
- GraphQL schema support

## Contributing

To extend the agent:

1. Subclass relevant analyzer classes
2. Override `generate_sample_value()` for custom types
3. Implement custom failure detection patterns
4. Add new test runners (Jenkins, GitLab CI, etc.)

## License

MIT License - See LICENSE file

## Support

For issues and questions:
- Check troubleshooting section above
- Review `agent-execution.log` 
- Enable debug mode for detailed traces
- Check WSDL and SoapUI project validity

---

**Version**: 1.0.0  
**Last Updated**: 2024-08-13  
**Maintainer**: SOAP Testing Team
