# Intelligent Regression Testing Agent

## Structure

- project/Intelligent-Regression-Testing-Agent.xml
- pom.xml
- .github/workflows/soapui-tests.yml

## Run Locally

```bash
mvn test
```

## Notes

- Endpoint and WSDL references should be parameterized for multi-environment execution.
- The project contains a CaseFile SOAP service test flow.
- priorityFlag is expected as a boolean value.
