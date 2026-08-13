# Quick Start Guide - SOAP Self-Healing Agent

## 5-Minute Setup

### 1. Prerequisites Check
```bash
# Verify you have the required tools
python3 --version          # Should be 3.7+
mvn --version              # Should be 3.6+
java -version              # Should be 8+
```

### 2. Navigate to Project
```bash
cd /workspaces/Intelligent-Regression-Testing-Agent
```

### 3. Run the Agent
```bash
# Option A: Using shell script (recommended)
chmod +x run-agent.sh
./run-agent.sh

# Option B: Direct Python execution
python3 soap-self-healing-agent.py

# Option C: Docker
docker-compose up soap-agent
```

## Expected Behavior

### First Run (With Failures)
```
[ITERATION 1/5]
[*] Running SOAP tests...
[!] Analyzing test failures...
  Failure 1: Missing required element 'priorityFlag'
[*] Fixing requests based on WSDL...
  [+] Added required field 'priorityFlag' = 'true'
[*] Project updated and saved
```

### Second Run (Tests Pass)
```
[ITERATION 2/5]
[*] Running SOAP tests...
[✓] ALL TESTS PASSED!
```

## Common Scenarios

### Scenario 1: New Required Field in WSDL

**What happens:**
1. WSDL is updated with new required field `caseStatus`
2. Old SOAP requests don't include it
3. Tests fail with "Missing element" error

**Agent fixes it by:**
1. Detecting the missing field in WSDL
2. Determining it's a required string field
3. Adding `<caseStatus>Active</caseStatus>` to request
4. Re-running tests ✓

### Scenario 2: Changed Field Type

**What happens:**
1. WSDL changes `age` from integer to string
2. Tests fail with type mismatch

**Agent fixes it by:**
1. Reading WSDL to see new type is string
2. Updating sample value from `25` to `"25"`
3. Re-running tests ✓

### Scenario 3: Multiple Failures

**What happens:**
1. Tests fail with 3 different assertion errors
2. Missing 2 fields, wrong type on 1 field

**Agent fixes it by:**
1. Analyzing all failures
2. Creating one comprehensive fix for all issues
3. Updating request once with all corrections
4. Re-running tests ✓

## Monitoring Execution

### View Progress in Real-Time
```bash
# In another terminal, watch the log file
tail -f agent-execution.log
```

### Check Project Updates
```bash
# Monitor changes to the SoapUI project
watch 'grep -c "priorityFlag" Intelligent-Regression-Testing-Agent-final.xml'
```

### Verify WSDL Analysis
```bash
# Run agent with verbose output
python3 soap-self-healing-agent.py --debug
```

## Testing the Agent

### Test 1: Verify WSDL Parsing
```python
# Quick test in Python
python3 << 'EOF'
from soap_self_healing_agent import WSDLAnalyzer

wsdl = WSDLAnalyzer('CaseFileService-v3-priorityMandatory.wsdl')
print(f"Service: {wsdl.service_name}")
print(f"Operations: {list(wsdl.operations.keys())}")

schema = wsdl.get_request_schema('createCaseFile')
print(f"Required fields: {wsdl.get_required_fields('createCaseFile')}")
EOF
```

### Test 2: Verify Test Execution
```bash
# Run Maven tests directly to ensure setup is correct
mvn clean test -DtestSuite="TestSuite 1"
```

### Test 3: Verify Request Fixing
```python
# Quick test of request fixing
python3 << 'EOF'
from soap_self_healing_agent import SoapRequestFixer, Element, ElementType

# Create a test element
elem = Element(
    name="priorityFlag",
    type_name="boolean",
    element_type=ElementType.BOOLEAN,
    is_required=True
)

# Generate sample value
value = SoapRequestFixer.generate_sample_value(elem)
print(f"Generated value for boolean field: {value}")
EOF
```

## Configuration Customization

### Increase Max Iterations
```json
{
  "execution": {
    "max_iterations": 10
  }
}
```

### Disable Sample Value Generation (keep manual values)
```json
{
  "request_fixing": {
    "auto_fix_missing_required_fields": true,
    "generate_sample_values": false
  }
}
```

### Speed Up Retries
```json
{
  "execution": {
    "retry_delay": 0.5
  }
}
```

## Troubleshooting

### Issue: "No WSDL file found"

**Cause:** WSDL file not in project root
```bash
# Check what files exist
ls -la *.wsdl

# If missing, copy it
cp /path/to/your/service.wsdl ./CaseFileService-v3-priorityMandatory.wsdl
```

### Issue: "No SoapUI project file found"

**Cause:** Project file doesn't have "final" in name
```bash
# Check project files
ls -la *.xml

# Rename if needed
mv Intelligent-Regression-Testing-Agent.xml Intelligent-Regression-Testing-Agent-final.xml
```

### Issue: "Maven command not found"

**Solution:** Install Maven
```bash
# On Ubuntu/Debian
sudo apt-get install maven

# On macOS
brew install maven

# Verify installation
mvn --version
```

### Issue: Tests timeout

**Solution:** Increase timeout
```json
{
  "execution": {
    "timeout": 120
  }
}
```

Or check if mock service is running on port 8088:
```bash
netstat -an | grep 8088
# If not running, check the SoapUI project endpoint configuration
```

### Issue: Agent completes but no fixes applied

**Cause:** Tests might not have failures to fix
```bash
# Verify test failures exist
mvn test 2>&1 | grep -i "fail\|error\|assert"

# Check WSDL is being read correctly
python3 -c "from soap_self_healing_agent import WSDLAnalyzer; WSDLAnalyzer('*.wsdl')" 2>&1 | head -20
```

## Integration Examples

### GitHub Actions Workflow
```yaml
name: SOAP Tests
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-java@v2
        with:
          java-version: '17'
      - run: |
          chmod +x run-agent.sh
          ./run-agent.sh
```

### GitLab CI Pipeline
```yaml
soap-test:
  image: openjdk:17
  script:
    - apt-get update && apt-get install -y python3 python3-pip maven
    - pip3 install -r requirements.txt
    - chmod +x run-agent.sh
    - ./run-agent.sh
  artifacts:
    paths:
      - agent-execution.log
```

### Jenkins Job
```groovy
node {
    stage('Checkout') {
        checkout scm
    }
    
    stage('SOAP Self-Healing Tests') {
        sh '''
            chmod +x run-agent.sh
            ./run-agent.sh
        '''
    }
    
    stage('Archive Results') {
        archiveArtifacts artifacts: 'agent-execution.log'
    }
}
```

## Performance Tips

1. **Parallel Execution**: Run multiple agents on different test suites
   ```bash
   ./run-agent.sh &
   # Agent runs in background
   ```

2. **Caching**: Maven caches dependencies
   ```bash
   mvn dependency:resolve
   ```

3. **Quick Validation**: Test Maven directly first
   ```bash
   mvn test -q  # Quiet mode, faster output
   ```

4. **Resource Limits**: For Docker/Kubernetes
   ```yaml
   resources:
     limits:
       memory: "1Gi"
       cpu: "500m"
   ```

## Next Steps

1. **Review AGENT-README.md** for detailed documentation
2. **Check agent-config.json** for all configuration options
3. **Explore soap-self-healing-agent.py** to customize behavior
4. **Set up CI/CD integration** using provided examples
5. **Monitor execution.log** for insights

## Getting Help

- Check **AGENT-README.md** for comprehensive documentation
- Review error messages in **agent-execution.log**
- Validate WSDL with `python3 -c "import xml.etree.ElementTree as ET; ET.parse('*.wsdl')"`
- Validate SoapUI project with `python3 -c "import xml.etree.ElementTree as ET; ET.parse('*.xml')"`
- Run tests manually: `mvn test -X` (with debug output)

## Support

For issues:
1. Gather logs: `cat agent-execution.log`
2. Check prerequisites: `./run-agent.sh --check`
3. Validate project files
4. Review troubleshooting section above
5. File an issue with logs attached

---

**Ready to go!** 🚀

Run `./run-agent.sh` to start the SOAP Self-Healing Agent now.
