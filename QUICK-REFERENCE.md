# SOAP Agent - Quick Reference Card

## 📋 Command Cheat Sheet

### Run Agent
```bash
./run-agent.sh                    # Recommended
python3 soap-self-healing-agent.py # Direct execution
docker-compose up                 # Docker
```

### Check Prerequisites
```bash
python3 --version                # Python 3.7+
mvn --version                    # Maven 3.6+
java -version                    # Java 8+
```

### View Logs
```bash
tail -f agent-execution.log       # Real-time logs
cat agent-execution.log           # Full log
```

### Verify WSDL
```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('*.wsdl'); print('✓ Valid')"
```

### Run Tests Manually
```bash
mvn test -DtestSuite="TestSuite 1"
mvn test -X                       # With debug output
```

### Update Configuration
```bash
# Edit agent-config.json
vim agent-config.json
```

## 🎯 Common Scenarios

### Scenario A: Add Missing Required Field
```
WSDL: <xsd:element name="priorityFlag" type="xsd:boolean"/>
Request: Missing <priorityFlag>
Fix: Agent adds <priorityFlag>true</priorityFlag>
Result: ✓ Tests pass
```

### Scenario B: Change Field Type
```
WSDL: type changed from "int" to "string"
Request: <count>123</count>
Fix: Agent generates <count>SampleValue</count>
Result: ✓ Tests pass
```

### Scenario C: Multiple Failures
```
Failures: 3 missing fields, 2 type mismatches
Fix: Agent fixes all 5 issues in one iteration
Result: ✓ Tests pass
```

## 🔧 Configuration Quick Edit

```bash
# Increase max iterations
sed -i 's/"max_iterations": 5/"max_iterations": 10/' agent-config.json

# Disable sample value generation
sed -i 's/"generate_sample_values": true/"generate_sample_values": false/' agent-config.json

# Increase timeout
sed -i 's/"timeout": 60/"timeout": 120/' agent-config.json
```

## 📊 Expected Output

```
[ITERATION 1/5]
[*] Running SOAP tests...
[*] Analyzing test failures...
[*] Analyzing WSDL and fixing requests...
[+] Project saved
[ITERATION 2/5]
[*] Running SOAP tests...
[✓] ALL TESTS PASSED!
```

## ⏱️ Typical Times

| Operation | Time |
|-----------|------|
| WSDL Analysis | ~100ms |
| Test Execution | 5-15s |
| Request Fixing | 50-100ms |
| Full Iteration | 5-20s |
| Success | 2 iterations |

## 🚨 Quick Troubleshooting

| Problem | Fix |
|---------|-----|
| No WSDL found | `ls *.wsdl` - check file exists |
| No project found | Ensure file has "final" in name |
| Maven not found | `apt-get install maven` |
| Port 8088 in use | Check mock service: `lsof -i :8088` |
| Tests timeout | Increase `timeout` in config |
| No fixes applied | Check `mvn test` runs independently |

## 📁 Key Files

| File | Purpose |
|------|---------|
| `soap-self-healing-agent.py` | Main agent |
| `run-agent.sh` | Shell launcher |
| `agent-config.json` | Configuration |
| `*.wsdl` | Service schema |
| `*-final.xml` | SoapUI project |
| `pom.xml` | Maven config |

## 📚 Documentation Map

```
README.md (Start Here)
    │
    ├─→ QUICKSTART.md (5-min setup)
    │       ├─→ Common scenarios
    │       ├─→ Troubleshooting
    │       └─→ CI/CD examples
    │
    ├─→ AGENT-README.md (Full docs)
    │       ├─→ Features
    │       ├─→ Architecture
    │       ├─→ Configuration
    │       └─→ Integration
    │
    └─→ DEVELOPER-GUIDE.md (Technical)
            ├─→ Components
            ├─→ Extensions
            ├─→ Testing
            └─→ Performance
```

## 🔄 Agent Flow

```
START
  ↓
ANALYZE WSDL
  ↓
RUN TESTS ──┐
  ↓         │
PASS? ──YES→ END ✓
  ↓ NO
EXTRACT FAILURES
  ↓
FIX REQUESTS
  ↓
SAVE PROJECT
  ↓
RETRY ──→ RUN TESTS
```

## 💻 Docker Quick Commands

```bash
# Build image
docker build -t soap-agent .

# Run with Docker Compose
docker-compose up

# Run and follow logs
docker-compose up --follow

# Run specific service
docker-compose up soap-agent

# Stop all containers
docker-compose down

# View logs
docker-compose logs -f
```

## 🔌 CI/CD Quick Snippets

### GitHub Actions
```yaml
- run: chmod +x run-agent.sh && ./run-agent.sh
```

### Jenkins
```groovy
sh 'chmod +x run-agent.sh && ./run-agent.sh'
```

### GitLab CI
```yaml
script:
  - chmod +x run-agent.sh
  - ./run-agent.sh
```

## 🎨 Customization

### Custom Sample Values
Edit `soap-self-healing-agent.py`:
```python
def generate_sample_value(element: Element) -> str:
    if element.name == "applicantName":
        return "John Doe"
    # ... more custom logic
```

### Custom WSDL Parsing
Extend `WSDLAnalyzer` class in `soap-self-healing-agent.py`

### Custom Failure Detection
Override `extract_failures()` method

## 📈 Performance Tuning

```bash
# Speed up retry loop
# Edit agent-config.json:
"retry_delay": 0.5    # From 2 seconds

# Increase parallelism (Future)
# Run multiple agents on different test suites
./run-agent.sh &
./run-agent.sh &
./run-agent.sh &
```

## 🎓 Learning Path

1. Read `README.md` (5 min)
2. Follow `QUICKSTART.md` (5 min)
3. Run agent once (5-20 min)
4. Review `AGENT-README.md` (20 min)
5. Study `DEVELOPER-GUIDE.md` (30 min)
6. Customize for your needs (varies)

## ✅ Verification Checklist

- [ ] Python 3.7+ installed
- [ ] Maven 3.6+ installed
- [ ] Java 8+ installed
- [ ] WSDL file exists
- [ ] SoapUI project exists
- [ ] run-agent.sh is executable
- [ ] agent-config.json is valid JSON
- [ ] Can run: `python3 soap-self-healing-agent.py`
- [ ] Can run: `./run-agent.sh`
- [ ] `mvn test` works independently

## 🎯 Next Steps

1. **Quick Test**
   ```bash
   ./run-agent.sh
   ```

2. **Review Results**
   ```bash
   cat agent-execution.log
   ```

3. **Customize Config**
   ```bash
   vim agent-config.json
   ```

4. **Integrate with CI/CD**
   Copy appropriate snippet from QUICKSTART.md

5. **Extend Agent**
   Follow examples in DEVELOPER-GUIDE.md

## 📞 Support Resources

| Resource | Use For |
|----------|---------|
| QUICKSTART.md | Immediate answers |
| AGENT-README.md | Feature details |
| DEVELOPER-GUIDE.md | Technical deep-dive |
| agent-execution.log | Debug information |
| agent-config.json | Configuration help |

## 🚀 Quick Start (TL;DR)

```bash
cd /workspaces/Intelligent-Regression-Testing-Agent
chmod +x run-agent.sh
./run-agent.sh
# Watch it work! ✨
```

---

**Print this card for quick reference!** 📋

**Last Updated:** 2024-08-13  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
