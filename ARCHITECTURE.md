```
╔════════════════════════════════════════════════════════════════════════════╗
║                  SOAP SELF-HEALING TEST AGENT v1.0                         ║
║         Intelligent Regression Testing Agent Architecture                 ║
╚════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│  INPUT FILES                                                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐        ┌──────────────────┐                          │
│  │  *.wsdl          │        │  *-final.xml     │                          │
│  │  ─────────────── │        │  ─────────────── │                          │
│  │ SOAP Service     │        │ SoapUI Project   │                          │
│  │ Schema           │        │ Test Cases       │                          │
│  │ Definitions      │        │ Test Assertions  │                          │
│  │ Operations       │        │ SOAP Requests    │                          │
│  └────────┬─────────┘        └─────────┬────────┘                          │
│           │                            │                                   │
└───────────┼────────────────────────────┼───────────────────────────────────┘
            │                            │
            ▼                            ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  AGENT CORE COMPONENTS                                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SoapSelfHealingAgent                             │   │
│  │                  (Main Orchestrator)                                │   │
│  │  ┌────────────────────────────────────────────────────────────┐    │   │
│  │  │ while iteration < max_iterations:                         │    │   │
│  │  │   1. Run Tests                                            │    │   │
│  │  │   2. Check if passed                                      │    │   │
│  │  │   3. Extract failures if any                              │    │   │
│  │  │   4. Get current SOAP requests                            │    │   │
│  │  │   5. For each request:                                    │    │   │
│  │  │      a. Identify operation                                │    │   │
│  │  │      b. Get WSDL schema                                   │    │   │
│  │  │      c. Fix request based on schema                       │    │   │
│  │  │      d. Update in project                                 │    │   │
│  │  │   6. Save project file                                    │    │   │
│  │  │   7. Wait and retry                                       │    │   │
│  │  └────────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                           ▲              ▲              ▲                   │
│                           │              │              │                   │
│        ┌──────────────────┘              │              └──────────────┐    │
│        │                                 │                            │    │
│        │                    ┌────────────┘──────────┐                │    │
│        ▼                    ▼                       ▼                ▼    │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐  ┌─────────┐  │
│  │ WSDLAnalyzer │  │SoapTestAnalyzer│  │ SoapRequestFixer │  │  Config │  │
│  ├──────────────┤  ├───────────────┤  ├──────────────────┤  ├─────────┤  │
│  │              │  │               │  │                  │  │ Max     │  │
│  │ Parses WSDL  │  │ Runs Maven     │  │ Generates fixed  │  │ iters:5 │  │
│  │ Schema       │  │ tests          │  │ SOAP requests    │  │ Retry   │  │
│  │              │  │               │  │                  │  │ delay:2 │  │
│  │ Extracts:    │  │ Parses output  │  │ Sample values:   │  │ Timeout:│  │
│  │ - Elements   │  │ for failures   │  │ - STRING:        │  │ 60s     │  │
│  │ - Types      │  │               │  │   "SampleValue"  │  │         │  │
│  │ - Required   │  │ Extracts      │  │ - BOOLEAN:       │  └─────────┘  │
│  │   fields     │  │ requests from  │  │   "true"         │                │
│  │ - Operations │  │ project        │  │ - INTEGER:       │                │
│  │              │  │               │  │   "123"          │                │
│  │ Required     │  │ Updates project│  │ - DATE:          │                │
│  │ field list   │  │ with fixes     │  │   "2024-08-13"   │                │
│  │              │  │               │  │                  │                │
│  └──────────────┘  └───────────────┘  └──────────────────┘                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
            │                       │                       │
            │                       │                       │
            ▼                       ▼                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  ITERATION CYCLE                                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ITERATION 1              ITERATION 2              ITERATION 3+            │
│  ┌───────────┐            ┌───────────┐           ┌──────────┐             │
│  │ Run Tests │ ──FAIL──▶  │  Analyze  │ ──FIX──▶  │ Re-run   │             │
│  │ (with     │            │ failures  │           │ Tests    │             │
│  │  old req) │            │ & WSDL    │           │ (with    │             │
│  └───────────┘            │ Schema    │           │  new     │             │
│                           │           │           │  req)    │             │
│   Missing:                │ Missing   │           └──┬───────┘             │
│   - priorityFlag          │ field:    │              │                     │
│   - status                │ - prio...◀─────────────Pass! ✓                │
│   Error:                  │ - status  │                                    │
│   Wrong type              │           │                                    │
│                           └───────────┘                                    │
│                           Fix applied:                                     │
│                           <priorityFlag>true</priorityFlag>               │
│                           <status>SUCCESS</status>                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
            │                                                 ▲
            │                                                 │
            └─────────────────── PROJECT FILE ──────────────┘
                         ┌──────────┬──────────┐
                         │          │          │
                         ▼          ▼          ▼
                      (Read)    (Update)   (Write)
                    Requests   w/ Fixes    to Disk


┌──────────────────────────────────────────────────────────────────────────────┐
│  DATA FLOW: WSDL → ANALYSIS → REQUEST FIX → PROJECT UPDATE                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WSDL                    Element Definition            Sample Request       │
│  ─────────────────────────────────────────────────────────────────────     │
│                                                                              │
│  <xsd:element            Element {                     <soapenv:Body>       │
│    name="priority        name: "priorityFlag"         <cas:createCaseFile>│
│    Flag"                 type: BOOLEAN                  <caseId>123</c...   │
│    type="xsd:boolean"/>  required: true                 <applicantName>...  │
│                        }                               <priorityFlag>    │
│                          ▼                              true            │
│                    Generate Sample:                    </priorityFlag>    │
│                    "true"                              </cas:create...    │
│                          │                             </soapenv:Body>   │
│                          └────────────────────────────────────┘            │
│                                                                              │
│  Status: ✓ Missing field added with correct type and sample value          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘


╔════════════════════════════════════════════════════════════════════════════╗
║                         EXECUTION FLOW                                      ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  START                                                                     ║
║    ↓                                                                       ║
║  Load WSDL + Project                                                       ║
║    ↓                                                                       ║
║  [ITERATION LOOP] ───────────────────────────┐                            ║
║    ↓                                         │                            ║
║  1. Run Tests via Maven                      │                            ║
║    ├─ Executes: mvn test                     │                            ║
║    └─ Captures: stdout + stderr              │                            ║
║       ↓                                      │                            ║
║  2. Parse Test Results                       │                            ║
║    ├─ All passed? ──YES──┐                  │                            ║
║    │                     │                  │                            ║
║    └─ Extract failures   │                  │                            ║
║       ↓                  │                  │                            ║
║  3. Analyze WSDL Schema  │                  │                            ║
║    ├─ Load WSDL file     │                  │                            ║
║    ├─ Parse elements     │                  │                            ║
║    ├─ Get required       │                  │                            ║
║    │  fields for each    │                  │                            ║
║    │  operation          │                  │                            ║
║    └─ Identify types     │                  │                            ║
║       ↓                  │                  │                            ║
║  4. Generate Fixes       │                  │                            ║
║    ├─ For each request:  │                  │                            ║
║    │  ├─ Extract         │                  │                            ║
║    │  │  operation name  │                  │                            ║
║    │  ├─ Get schema      │                  │                            ║
║    │  ├─ Find missing    │                  │                            ║
║    │  │  required fields │                  │                            ║
║    │  └─ Add fields with │                  │                            ║
║    │     sample values   │                  │                            ║
║    └─ Any fixes made? NO │                  │                            ║
║       │         YES      │                  │                            ║
║       ▼         ↓        │                  │                            ║
║     END     5. Update    │                  │                            ║
║    FAILED    Project     │                  │                            ║
║       ▲       ├─ Write   │                  │                            ║
║       │       │  updated │                  │                            ║
║       │       │  requests│                  │                            ║
║       │       │  to XML  │                  │                            ║
║       │       └─ Save    │                  │                            ║
║       │          file    │                  │                            ║
║       │          ↓       │                  │                            ║
║       │       6. Wait    │                  │                            ║
║       │       (retry_    │                  │                            ║
║       │        delay)    │                  │                            ║
║       │          ↓       │                  │                            ║
║       └──────← Retry ←───┘ (next iteration)                              ║
║                │                                                           ║
║                └─ MAX ITERATIONS?                                         ║
║                   YES: END (MAX REACHED)                                  ║
║                   NO: Continue loop                                       ║
║                                                                            ║
║  Report Results                                                            ║
║    ↓                                                                       ║
║  END                                                                       ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

## Architecture Legend

### Components

- **WSDLAnalyzer**: Intelligent WSDL parser
  - Reads XSD schema definitions
  - Extracts element types and requirements
  - Identifies required vs optional fields
  - Determines data type for each field

- **SoapTestAnalyzer**: Test execution manager
  - Runs tests via Maven
  - Parses test output
  - Extracts SOAP requests
  - Detects failures and errors
  - Updates project file

- **SoapRequestFixer**: Request generator
  - Analyzes SOAP request structure
  - Identifies missing fields
  - Generates type-appropriate sample values
  - Creates corrected SOAP XML

- **SoapSelfHealingAgent**: Main orchestrator
  - Controls iteration loop
  - Coordinates all components
  - Manages retries and timing
  - Tracks history and logs results

### Data Models

- **Element**: Represents WSDL element definition
  - name: Field name
  - type_name: XSD type string
  - element_type: Parsed type enum
  - is_required: Boolean flag
  - children: Child elements for complex types

- **ElementType**: Enum of supported types
  - STRING
  - BOOLEAN
  - INTEGER
  - DECIMAL
  - DATE
  - DATETIME
  - COMPLEX

### Execution Phases

1. **Initialization**: Load WSDL and project files
2. **Test Execution**: Run tests and capture results
3. **Analysis**: Parse failures and WSDL schema
4. **Fixing**: Generate corrected requests
5. **Update**: Save fixes to project file
6. **Iteration**: Repeat until success or max attempts

### Key Algorithms

**WSDL Analysis**:
1. Parse XML namespaces
2. Locate schema element
3. Extract all XSD elements
4. For each element:
   - Determine if simple or complex
   - If complex, parse child elements
   - Extract type information
   - Determine required status

**Request Fixing**:
1. Parse current SOAP request XML
2. Locate request element in body
3. Compare with WSDL schema
4. For each missing required field:
   - Generate appropriate sample value
   - Add to request XML
5. Return updated request

**Iteration Loop**:
1. Run tests → Parse results
2. If pass → Success, exit
3. If fail → Extract failures
4. Analyze WSDL for each operation
5. Fix all requests
6. Save project
7. Wait and retry (back to step 1)

---

**This is a complex but well-architected system that handles SOAP testing automation intelligently!** ✨
