# Intelligent Regression Testing Agent

## 🚀 Quick Start

**SOAP Self-Healing Test Agent** - Automatically fixes failing SOAP tests by analyzing WSDL schemas and auto-correcting requests!

```bash
# Run the intelligent agent
chmod +x run-agent.sh
./run-agent.sh
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[QUICKSTART.md](QUICKSTART.md)** | 5-minute setup and common scenarios |
| **[AGENT-README.md](AGENT-README.md)** | Complete agent documentation |
| **[DEVELOPER-GUIDE.md](DEVELOPER-GUIDE.md)** | Architecture and extension guide |

## ✨ Features

- **🧠 Intelligent Analysis**: Automatically parses WSDL to understand service schema
- **🔍 Failure Detection**: Identifies SOAP faults and assertion failures  
- **🔧 Auto-Fix**: Generates correct SOAP requests based on WSDL requirements
- **🔁 Iterative Healing**: Re-runs tests after fixes until all pass
- **📊 Detailed Logging**: Tracks all iterations and failures
- **🐳 Docker Support**: Run in containers for CI/CD integration

## 🏗️ Project Structure

```
.
├── soap-self-healing-agent.py          # Main agent implementation
├── run-agent.sh                        # Shell launcher script
├── agent-config.json                   # Configuration file
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # Container image
├── docker-compose.yml                  # Docker Compose setup
├── CaseFileService-v3-priorityMandatory.wsdl   # WSDL schema
├── Intelligent-Regression-Testing-Agent-final.xml # SoapUI project
├── pom.xml                             # Maven configuration
├── QUICKSTART.md                       # Quick start guide
├── AGENT-README.md                     # Complete documentation
├── DEVELOPER-GUIDE.md                  # Developer documentation
└── README.md                           # This file
```

## 🔄 How It Works

```
1. RUN TESTS
   └─ Execute SOAP tests from SoapUI project
   
2. CHECK RESULTS
   └─ Did tests pass? YES → Success! | NO → Continue
   
3. ANALYZE FAILURES
   └─ Extract error messages and missing fields
   
4. PARSE WSDL
   └─ Read schema to understand requirements
   
5. FIX REQUESTS
   └─ Add missing required fields with correct types
   └─ Generate appropriate sample values
   
6. SAVE & RETRY
   └─ Update project and re-run tests
   └─ Repeat until success or max iterations reached
```

## 🚀 Usage

### Basic Execution

```bash
# Using shell script (recommended)
./run-agent.sh

# Or directly with Python
python3 soap-self-healing-agent.py

# Or with Docker
docker-compose up soap-agent
```

### Expected Output

```
======================================================================
INTELLIGENT SOAP SELF-HEALING TEST AGENT
======================================================================
Service: CaseFileService
WSDL: CaseFileService-v3-priorityMandatory.wsdl
Project: Intelligent-Regression-Testing-Agent-final.xml
======================================================================

[ITERATION 1/5]
[*] Running SOAP tests...
[*] Analyzing test failures...
  Failure 1: Missing required element 'priorityFlag'
[*] Analyzing WSDL and fixing requests...
  [+] Added required field 'priorityFlag' = 'true'
  [+] Updated request
[+] Project saved

[ITERATION 2/5]
[*] Running SOAP tests...
[✓] ALL TESTS PASSED!

======================================================================
SUCCESS! All tests passed on iteration 2
======================================================================
```

## 📋 Prerequisites

- Python 3.7+
- Maven 3.6+
- Java 8+
- WSDL file
- SoapUI project file

## 🔧 Configuration

Edit `agent-config.json` to customize behavior:

```json
{
  "execution": {
    "max_iterations": 5,
    "retry_delay": 2,
    "timeout": 60
  },
  "request_fixing": {
    "auto_fix_missing_required_fields": true,
    "generate_sample_values": true
  }
}
```

## 🐳 Docker

```bash
# Build image
docker build -t soap-agent .

# Run with Docker Compose
docker-compose up

# Run with custom command
docker run -v $(pwd):/app soap-agent ./run-agent.sh
```

## 🔌 Integration

### GitHub Actions

```yaml
- name: Run SOAP Self-Healing Tests
  run: |
    chmod +x run-agent.sh
    ./run-agent.sh
```

The repository now includes an automated workflow at `/home/runner/work/Intelligent-Regression-Testing-Agent/Intelligent-Regression-Testing-Agent/.github/workflows/soapui-tests.yml` that:
- triggers on WSDL, SoapUI project, and agent changes
- runs the self-healing agent through `./run-agent.sh`
- publishes `agent-execution.log` and the healed SoapUI project as artifacts
- persists healed SoapUI assets back to the branch on push events

### Healing Scope

The agent is restricted to SOAP test assets only:
- SoapUI project XML updates
- request payload healing
- endpoint synchronization from the WSDL

It does not rewrite business/service implementation code.

### Jenkins

```groovy
stage('SOAP Tests') {
    steps {
        sh 'chmod +x run-agent.sh && ./run-agent.sh'
    }
}
```

### GitLab CI

```yaml
soap-test:
  script:
    - chmod +x run-agent.sh
    - ./run-agent.sh
  artifacts:
    paths:
      - agent-execution.log
```

## 📝 Traditional Execution

For manual testing with Maven:

```bash
mvn test
```

## 📚 Project Components

- **CaseFileService-v3-priorityMandatory.wsdl**: SOAP service definition (v3 with required priorityFlag)
- **Intelligent-Regression-Testing-Agent-final.xml**: SoapUI project with test cases
- **pom.xml**: Maven build configuration with test runner
- **agent-config.json**: Agent behavior configuration

## 🎯 Supported Scenarios

### Scenario 1: Missing Required Field
- WSDL adds new required field
- Agent detects it's missing from request
- Auto-adds field with appropriate sample value
- Tests pass ✓

### Scenario 2: Changed Field Type
- WSDL changes field type (e.g., int → string)
- Agent detects type mismatch
- Auto-generates correct sample value for new type
- Tests pass ✓

### Scenario 3: Multiple Failures
- Multiple assertions fail simultaneously
- Agent analyzes all failures
- Fixes all issues in one iteration
- Tests pass ✓

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No WSDL file found" | Ensure WSDL is in project root: `ls *.wsdl` |
| "No SoapUI project found" | Rename project with "final": `mv *.xml *-final.xml` |
| "Maven command not found" | Install Maven: `apt-get install maven` |
| Tests timeout | Increase timeout in `agent-config.json` |
| Port 8088 in use | Check mock service: `netstat -an \| grep 8088` |

See [QUICKSTART.md](QUICKSTART.md#troubleshooting) for more solutions.

## 📖 Full Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup, scenarios, troubleshooting
- **[AGENT-README.md](AGENT-README.md)** - Complete feature documentation
- **[DEVELOPER-GUIDE.md](DEVELOPER-GUIDE.md)** - Architecture, extensions, testing

## 🔬 How the Agent Fixes Tests

### Example: Missing Required Field

**WSDL Schema:**
```xml
<xsd:element name="createCaseFileRequest">
  <xsd:sequence>
    <xsd:element name="priorityFlag" type="xsd:boolean"/>
  </xsd:sequence>
</xsd:element>
```

**Original Request (Failing):**
```xml
<soapenv:Body>
  <cas:createCaseFileRequest>
    <caseId>123</caseId>
    <applicantName>John</applicantName>
  </cas:createCaseFileRequest>
</soapenv:Body>
```

**Agent Analysis:**
- Detects missing `priorityFlag` in request
- Checks WSDL: it's required ✓
- Determines type is boolean ✓

**Fixed Request:**
```xml
<soapenv:Body>
  <cas:createCaseFileRequest>
    <caseId>123</caseId>
    <applicantName>John</applicantName>
    <priorityFlag>true</priorityFlag>  <!-- ADDED -->
  </cas:createCaseFileRequest>
</soapenv:Body>
```

**Result:** Tests pass! ✓

## 💡 Key Capabilities

### WSDL Analysis
- Parses complex type definitions
- Extracts required vs optional fields
- Determines field data types
- Handles nested elements

### Failure Detection
- Parses Maven test output
- Identifies SOAP faults
- Recognizes assertion failures
- Tracks multiple errors

### Request Fixing
- Generates type-appropriate values
- Boolean → "true"
- String → "SampleValue"
- Date → "2024-08-13"
- Preserves existing correct values

### Iterative Healing
- Re-runs tests after each fix
- Configurable retry limit (default 5)
- Tracks success/failure history
- Logs all iterations

## 📊 Agent Performance

- WSDL Analysis: ~100ms
- Test Execution: 5-15 seconds
- Request Fixing: 50-100ms per request
- Full Iteration: 5-20 seconds

## 🛠️ Customization

Extend the agent for custom needs:

```python
# Custom sample values
class MyFixer(SoapRequestFixer):
    @staticmethod
    def generate_sample_value(element: Element) -> str:
        if element.name == "applicantName":
            return "Jane Doe"
        return super().generate_sample_value(element)

# Custom WSDL parsing
class MyAnalyzer(WSDLAnalyzer):
    def _parse_elements(self) -> Dict[str, Element]:
        elements = super()._parse_elements()
        # Custom logic
        return elements
```

See [DEVELOPER-GUIDE.md](DEVELOPER-GUIDE.md) for full extension examples.

## 🎓 Learning Resources

- [SOAP Protocol Basics](https://www.w3.org/TR/soap12/)
- [WSDL Specification](https://www.w3.org/TR/wsdl)
- [XML Schema Tutorial](https://www.w3.org/XML/Schema)
- [SoapUI Getting Started](https://www.soapui.org/getting-started)

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

## 📧 Support

For issues or questions:
- Review [QUICKSTART.md](QUICKSTART.md#troubleshooting)
- Check [AGENT-README.md](AGENT-README.md)
- Consult [DEVELOPER-GUIDE.md](DEVELOPER-GUIDE.md)
- Enable debug logging

## 🔗 Related Files

- **WSDL**: [CaseFileService-v3-priorityMandatory.wsdl](CaseFileService-v3-priorityMandatory.wsdl)
- **SoapUI Project**: [Intelligent-Regression-Testing-Agent-final.xml](Intelligent-Regression-Testing-Agent-final.xml)
- **Build Config**: [pom.xml](pom.xml)

---

**Version:** 1.0.0  
**Last Updated:** 2024-08-13  

🚀 **Ready to go!** Run `./run-agent.sh` to start the intelligent SOAP testing agent.
