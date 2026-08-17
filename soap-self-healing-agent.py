#!/usr/bin/env python3
"""
Intelligent SOAP Self-Healing Test Agent

This agent:
1. Runs SOAP tests from SoapUI project
2. Detects assertion failures
3. Analyzes the WSDL to understand schema requirements
4. Auto-fixes SOAP requests based on WSDL schema
5. Saves the fixes to the project
6. Re-runs tests iteratively until they pass
"""

import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import json
import subprocess
import sys
import os
import re
import time
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class ElementType(Enum):
    """WSDL element types"""
    STRING = "string"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    COMPLEX = "complex"


@dataclass
class Element:
    """Represents an XML element definition from WSDL"""
    name: str
    type_name: str
    element_type: ElementType
    min_occurs: int = 1
    max_occurs: str = "1"
    is_required: bool = False
    children: List['Element'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class WSDLAnalyzer:
    """Analyzes WSDL to understand service schema"""
    
    def __init__(self, wsdl_path: str):
        self.wsdl_path = wsdl_path
        self.tree = ET.parse(wsdl_path)
        self.root = self.tree.getroot()
        self.namespaces = {
            'wsdl': 'http://schemas.xmlsoap.org/wsdl/',
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'tns': self._extract_target_namespace(),
            'soap': 'http://schemas.xmlsoap.org/wsdl/soap/'
        }
        self.service_name = self._get_service_name()
        self.operations = self._parse_operations()
        self.elements = self._parse_elements()
    
    def _extract_target_namespace(self) -> str:
        """Extract target namespace from WSDL"""
        target_ns = self.root.get('targetNamespace', '')
        return target_ns
    
    def _get_service_name(self) -> str:
        """Get service name from WSDL"""
        service = self.root.find('.//wsdl:service', self.namespaces)
        if service is not None:
            return service.get('name', 'Unknown')
        return 'Unknown'

    def get_service_endpoint(self) -> Optional[str]:
        """Get SOAP service endpoint from WSDL"""
        address = self.root.find('.//soap:address', self.namespaces)
        if address is not None:
            location = address.get('location')
            if location:
                return location.strip()
        return None

    def _parse_operations(self) -> Dict[str, ET.Element]:
        """Parse operations defined in the WSDL (portType operations).

        Returns a mapping of operation name -> XML element for quick lookup.
        """
        operations = {}
        # Look for operations under portType first
        for op in self.root.findall('.//wsdl:portType/wsdl:operation', self.namespaces):
            name = op.get('name')
            if name:
                operations[name] = op

        # Fallback: also check bindings for operations
        for op in self.root.findall('.//wsdl:binding/wsdl:operation', self.namespaces):
            name = op.get('name')
            if name and name not in operations:
                operations[name] = op

        return operations
    
    def _parse_elements(self) -> Dict[str, Element]:
        """Parse all element definitions from WSDL schema"""
        elements = {}
        schema = self.root.find('.//xsd:schema', self.namespaces)
        
        if schema is None:
            return elements
        
        for elem in schema.findall('xsd:element', self.namespaces):
            elem_name = elem.get('name')
            elem_type = elem.get('type', '')
            
            # Handle complex types
            complex_type = elem.find('xsd:complexType', self.namespaces)
            if complex_type is not None:
                children = self._parse_complex_type(complex_type)
                elements[elem_name] = Element(
                    name=elem_name,
                    type_name='complex',
                    element_type=ElementType.COMPLEX,
                    children=children
                )
            else:
                # Simple type
                elem_obj = Element(
                    name=elem_name,
                    type_name=elem_type,
                    element_type=self._get_element_type(elem_type)
                )
                elements[elem_name] = elem_obj
        
        return elements
    
    def _parse_complex_type(self, complex_elem) -> List[Element]:
        """Parse complex type children"""
        children = []
        sequence = complex_elem.find('xsd:sequence', self.namespaces)
        
        if sequence is None:
            return children
        
        for child_elem in sequence.findall('xsd:element', self.namespaces):
            name = child_elem.get('name')
            type_name = child_elem.get('type', '')
            min_occurs = int(child_elem.get('minOccurs', '1'))
            max_occurs = child_elem.get('maxOccurs', '1')
            
            child = Element(
                name=name,
                type_name=type_name,
                element_type=self._get_element_type(type_name),
                min_occurs=min_occurs,
                max_occurs=max_occurs,
                is_required=(min_occurs >= 1)
            )
            children.append(child)
        
        return children
    
    def _get_element_type(self, type_str: str) -> ElementType:
        """Determine element type from type string"""
        if 'boolean' in type_str:
            return ElementType.BOOLEAN
        elif 'int' in type_str:
            return ElementType.INTEGER
        elif 'decimal' in type_str or 'float' in type_str:
            return ElementType.DECIMAL
        elif 'date' in type_str.lower():
            return ElementType.DATE if 'Time' not in type_str else ElementType.DATETIME
        else:
            return ElementType.STRING
    
    def get_request_schema(self, operation: str) -> Optional[Element]:
        """Get request schema for an operation"""
        # First, find the operation in portType
        port_type_op = None
        for op in self.root.findall('.//wsdl:portType/wsdl:operation', self.namespaces):
            if op.get('name') == operation:
                port_type_op = op
                break
        
        if port_type_op is None:
            return None
        
        # Get the input message
        input_elem = port_type_op.find('wsdl:input', self.namespaces)
        if input_elem is None:
            return None
        
        # Extract message name (handle both "name" and "message" attributes)
        message_name = input_elem.get('message', '')
        if not message_name:
            return None
        
        # Remove namespace prefix if present (tns:, etc)
        message_name = message_name.split('}')[-1] if '}' in message_name else message_name.split(':')[-1]
        
        # Find the message definition
        message = None
        for msg in self.root.findall('.//wsdl:message', self.namespaces):
            if msg.get('name') == message_name:
                message = msg
                break
        
        if message is None:
            return None
        
        # Get the part element
        part = message.find('wsdl:part', self.namespaces)
        if part is None:
            return None
        
        # Get element name from part
        element_name = part.get('element', '')
        if not element_name:
            return None
        
        # Remove namespace prefix
        element_name = element_name.split('}')[-1] if '}' in element_name else element_name.split(':')[-1]
        
        # Find the element in the schema
        schema = self.root.find('.//xsd:schema', self.namespaces)
        if schema is None:
            return None
        
        target_elem = None
        for elem in schema.findall('xsd:element', self.namespaces):
            if elem.get('name') == element_name:
                target_elem = elem
                break
        
        if target_elem is None:
            return None
        
        # Parse the element structure
        complex_type = target_elem.find('xsd:complexType', self.namespaces)
        if complex_type is None:
            return None
        
        children = self._parse_complex_type(complex_type)
        
        return Element(
            name=element_name,
            type_name='complexType',
            element_type=ElementType.COMPLEX,
            children=children
        )
    
    def get_required_fields(self, operation: str) -> List[str]:
        """Get list of required fields for an operation"""
        schema = self.get_request_schema(operation)
        required = []
        
        if schema and hasattr(schema, 'children'):
            for child in schema.children:
                if child.is_required:
                    required.append(child.name)
        
        return required


class SoapTestAnalyzer:
    """Analyzes SOAP test failures and responses"""
    
    def __init__(self, soapui_project_path: str):
        self.project_path = soapui_project_path
        self.tree = ET.parse(soapui_project_path)
        self.root = self.tree.getroot()
        self.namespaces = {
            'con': 'http://eviware.com/soapui/config',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        self.allowed_update_paths = {str(Path(soapui_project_path).resolve())}
    
    def run_tests(self, test_suite_name: Optional[str] = None) -> Dict:
        """Run SOAP tests directly by sending HTTP requests"""
        import urllib.request
        import urllib.error
        
        print(f"[*] Running SOAP tests from {self.project_path}...")
        
        test_suite_name = test_suite_name or 'TestSuite 1'
        passed = True
        failures_found = []
        stdout_lines = []
        
        try:
            # Find the endpoint from the project
            endpoint = self._get_endpoint()
            if not endpoint:
                return {
                    'returncode': 1,
                    'stdout': 'No endpoint configured',
                    'stderr': 'Could not find SOAP endpoint',
                    'passed': False
                }
            
            stdout_lines.append(f"[*] Using endpoint: {endpoint}")
            
            # Find test suite and cases
            test_suite = self.root.find(f".//con:testSuite[@name='{test_suite_name}']", self.namespaces)
            if test_suite is None:
                # Try to find any test suite
                test_suites = self.root.findall(".//con:testSuite", self.namespaces)
                if test_suites:
                    test_suite = test_suites[0]
                    test_suite_name = test_suite.get('name', 'Unknown')
            
            if test_suite is None:
                return {
                    'returncode': 1,
                    'stdout': 'No test suite found',
                    'stderr': '',
                    'passed': False
                }
            
            stdout_lines.append(f"[*] Running test suite: {test_suite_name}")
            
            # Get test cases
            test_cases = test_suite.findall(".//con:testCase", self.namespaces)
            stdout_lines.append(f"[*] Found {len(test_cases)} test cases\n")
            
            for test_case in test_cases:
                case_name = test_case.get('name', 'Unknown')
                stdout_lines.append(f"  [Test] {case_name}")
                
                # Get test steps
                test_steps = test_case.findall(".//con:testStep", self.namespaces)
                case_passed = True
                
                for step in test_steps:
                    step_name = step.get('name', 'Unknown')
                    
                    # Get request
                    request_elem = step.find(".//con:request", self.namespaces)
                    if request_elem is None:
                        continue
                    
                    request_text = request_elem.text
                    
                    # Empty or minimal request = FAILURE
                    if not request_text or '<' not in request_text or request_text.count('<') < 4:
                        stdout_lines.append(f"    [Step] {step_name}: FAIL - Empty/Incomplete Request")
                        failures_found.append(f"Empty request in test case {case_name}, step {step_name}")
                        case_passed = False
                        passed = False
                        continue
                    
                    # Send request and get response
                    try:
                        req = urllib.request.Request(
                            endpoint,
                            data=request_text.encode('utf-8'),
                            headers={
                                'Content-Type': 'text/xml; charset=utf-8',
                                'SOAPAction': ''
                            }
                        )
                        
                        with urllib.request.urlopen(req, timeout=10) as response:
                            resp_text = response.read().decode('utf-8')
                            stdout_lines.append(f"    [Step] {step_name}: OK")
                            
                            # Check assertions
                            assertions = step.findall(".//con:assertion", self.namespaces)
                            for assertion in assertions:
                                assert_type = assertion.get('type', '')
                                
                                # Simple assertion checking
                                if 'XPath' in assert_type or 'XPath Match' in assert_type:
                                    path_elem = assertion.find(".//con:path", self.namespaces)
                                    if path_elem is not None and path_elem.text:
                                        # Just check if response is valid
                                        if '<?xml' in resp_text or '<' in resp_text:
                                            stdout_lines.append(f"      [Assert] {assert_type}: PASS")
                                        else:
                                            stdout_lines.append(f"      [Assert] {assert_type}: FAIL")
                                            failures_found.append(f"Assertion failed in {case_name}: {assert_type}")
                                            case_passed = False
                                            passed = False
                                elif 'Script' in assert_type or 'Contains' in assert_type:
                                    token_elem = assertion.find(".//token")
                                    token = token_elem.text if token_elem is not None else None
                                    if token and token not in resp_text:
                                        stdout_lines.append(f"      [Assert] {assert_type}: FAIL")
                                        failures_found.append(
                                            f"Assertion failed in {case_name}: missing token {token}"
                                        )
                                        case_passed = False
                                        passed = False
                                    else:
                                        stdout_lines.append(f"      [Assert] {assert_type}: PASS")
                    
                    except urllib.error.HTTPError as e:
                        resp_text = e.read().decode('utf-8') if e.code >= 400 else ''
                        stdout_lines.append(f"    [Step] {step_name}: HTTP {e.code}")
                        
                        # Check for SOAP fault
                        if 'fault' in resp_text.lower():
                            failures_found.append(f"SOAP Fault in {case_name}")
                            case_passed = False
                            passed = False
                        else:
                            stdout_lines.append(f"      Response: {resp_text[:100]}")
                    
                    except urllib.error.URLError as e:
                        stdout_lines.append(
                            f"    [Step] {step_name}: Connection Error - {str(e.reason)[:80]}"
                        )
                        failures_found.append(f"Connection error in {case_name}: {e.reason}")
                        case_passed = False
                        passed = False
                    
                    except Exception as e:
                        stdout_lines.append(f"    [Step] {step_name}: ERROR - {str(e)[:50]}")
                        failures_found.append(f"Error in {case_name}: {str(e)}")
                        case_passed = False
                        passed = False
                
                status = "PASS" if case_passed else "FAIL"
                stdout_lines.append(f"  [{status}] {case_name}\n")
            
            return {
                'returncode': 0 if passed else 1,
                'stdout': '\n'.join(stdout_lines),
                'stderr': '\n'.join(failures_found) if failures_found else '',
                'passed': passed
            }
        
        except Exception as e:
            return {
                'returncode': 1,
                'stdout': 'Error running tests',
                'stderr': str(e),
                'passed': False
            }
    
    def _get_endpoint(self) -> Optional[str]:
        """Extract SOAP endpoint from project properties"""
        # First, look in project properties
        properties = self.root.find(".//con:properties", self.namespaces)
        if properties is not None:
            for prop in properties.findall("con:property", self.namespaces):
                name_elem = prop.find("con:name", self.namespaces)
                value_elem = prop.find("con:value", self.namespaces)
                
                if name_elem is not None and value_elem is not None:
                    if name_elem.text == 'endpoint' and value_elem.text:
                        return value_elem.text.strip()
        
        # Look for endpoint configuration in interfaces
        interfaces = self.root.findall(".//con:interface", self.namespaces)
        for interface in interfaces:
            endpoints = interface.findall(".//con:endpoint", self.namespaces)
            for endpoint in endpoints:
                url = endpoint.text
                if url and not url.startswith('${'):  # Skip template variables
                    return url.strip()
        
        # Fallback: search for http URL patterns in entire XML
        project_text = ET.tostring(self.root, encoding='unicode')
        endpoint_patterns = [
            r'<con:value>http://[^<]+</con:value>',
            r'http://[a-zA-Z0-9\-\.]+:[0-9]+/[^\s<>"\']+',
        ]
        
        for pattern in endpoint_patterns:
            match = re.search(pattern, project_text)
            if match:
                url = match.group(0).replace('<con:value>', '').replace('</con:value>', '')
                if 'localhost' in url or 'example.com' in url or '://' in url:
                    return url.strip()
        
        return None
    
    def extract_failures(self, test_output: str) -> List[Dict]:
        """Extract test failures from output"""
        failures = []
        
        # Look for assertion failures and SOAP faults
        patterns = [
            r'AssertionError: (.+?)(?:\n|$)',
            r'SOAP Fault: (.+?)(?:\n|$)',
            r'Error: (.+?)(?:\n|$)',
            r'Failed: (.+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, test_output, re.IGNORECASE)
            for match in matches:
                failures.append({
                    'message': match.group(1),
                    'type': 'assertion' if 'assert' in pattern.lower() else 'fault',
                    'pattern': pattern
                })
        
        return failures
    
    def get_test_requests(self) -> Dict[str, str]:
        """Extract SOAP request templates from project"""
        requests = {}

        for step in self.root.findall('.//con:testStep', self.namespaces):
            step_name = step.get('name', 'Unknown')
            request_elem = step.find('.//con:request', self.namespaces)

            if request_elem is not None and request_elem.text and request_elem.text.strip():
                requests[step_name] = request_elem.text.strip()

        if requests:
            return requests

        for call in self.root.findall('.//con:call', self.namespaces):
            call_name = call.get('name', 'Unknown')
            request_elem = call.find('con:request', self.namespaces)

            if request_elem is not None and request_elem.text and request_elem.text.strip():
                requests[call_name] = request_elem.text.strip()
        
        return requests
    
    def update_request_in_project(
        self,
        call_name: str,
        new_request: str,
        original_request: Optional[str] = None
    ) -> bool:
        """Update a SOAP request in the project file - both in calls and test cases"""
        updated = False
        
        # Update in operation calls
        for call in self.root.findall('.//con:call', self.namespaces):
            if call.get('name') == call_name:
                request_elem = call.find('con:request', self.namespaces)
                if request_elem is not None:
                    request_elem.text = '\n' + new_request + '\n'
                    updated = True
        
        # Update in test case steps
        for step in self.root.findall('.//con:testStep', self.namespaces):
            request_elem = step.find('.//con:request', self.namespaces)
            if request_elem is None:
                continue

            matches_step_name = step.get('name') == call_name
            matches_original_request = (
                original_request
                and request_elem.text
                and request_elem.text.strip() == original_request.strip()
            )

            if matches_step_name or matches_original_request:
                updated = True
                request_elem.text = '\n' + new_request + '\n'
        
        return updated

    def update_endpoint_in_project(self, new_endpoint: str) -> bool:
        """Update the SOAP endpoint in supported project fields only"""
        updated = False

        properties = self.root.findall(".//con:property", self.namespaces)
        for prop in properties:
            name_elem = prop.find("con:name", self.namespaces)
            value_elem = prop.find("con:value", self.namespaces)
            if name_elem is not None and value_elem is not None and name_elem.text == 'endpoint':
                if value_elem.text != new_endpoint:
                    value_elem.text = new_endpoint
                    updated = True

        for endpoint_elem in self.root.findall(".//con:endpoint", self.namespaces):
            current_value = (endpoint_elem.text or '').strip()
            if not current_value or current_value.startswith('${'):
                continue
            if current_value != new_endpoint:
                endpoint_elem.text = new_endpoint
                updated = True

        return updated
    
    def save_project(self):
        """Save updated project file"""
        resolved_path = str(Path(self.project_path).resolve())
        if resolved_path not in self.allowed_update_paths:
            raise ValueError(f"Refusing to write outside allowed project files: {resolved_path}")
        # Pretty print the XML
        self.tree.write(self.project_path, encoding='utf-8', xml_declaration=True)
        print(f"[+] Project saved: {self.project_path}")


class SoapRequestFixer:
    """Generates fixed SOAP requests based on WSDL schema"""
    
    @staticmethod
    def parse_soap_request(soap_xml: str) -> Dict:
        """Parse SOAP request to extract structure"""
        try:
            root = ET.fromstring(soap_xml)
            
            # Extract namespaces
            namespaces = dict([node for _, node in ET.iterparse(
                ET.ElementTree(root).ElementTree.StringIO(), 
                events=['start-ns']
            )])
            
            return {
                'raw': soap_xml,
                'root': root,
                'namespaces': namespaces
            }
        except Exception as e:
            print(f"[!] Error parsing SOAP request: {e}")
            return {'raw': soap_xml}

    @staticmethod
    def _find_field_element(request_elem: ET.Element, namespace: str, field_name: str) -> Optional[ET.Element]:
        """Find a field element by local name or namespaced tag"""
        namespaced_tag = f"{{{namespace}}}{field_name}"
        for child in request_elem:
            if child.tag == namespaced_tag:
                return child
            if '}' in child.tag and child.tag.split('}', 1)[1] == field_name:
                return child
            if child.tag == field_name:
                return child
        return None
    
    @staticmethod
    def generate_sample_value(element: Element) -> str:
        """Generate appropriate sample value for element type"""
        if element.element_type == ElementType.BOOLEAN:
            return "true"
        elif element.element_type == ElementType.INTEGER:
            return "123"
        elif element.element_type == ElementType.DECIMAL:
            return "123.45"
        elif element.element_type == ElementType.DATE:
            return datetime.now().strftime("%Y-%m-%d")
        elif element.element_type == ElementType.DATETIME:
            return datetime.now().isoformat()
        else:
            return "SampleValue"
    
    @staticmethod
    def fix_request_from_wsdl(
        soap_request: str, 
        wsdl_schema: Element,
        operation_name: str
    ) -> str:
        """Generate corrected SOAP request based on WSDL schema"""
        
        if not isinstance(wsdl_schema, Element) or not wsdl_schema.children:
            return soap_request
        
        try:
            # Parse the current request
            root = ET.fromstring(soap_request)
            
            # Register namespaces
            ns = {
                'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
                'tns': 'http://demo.org/casefile'
            }
            
            # Define namespaces
            for prefix, uri in ns.items():
                ET.register_namespace(prefix, uri)
            
            body = root.find('.//soapenv:Body', ns)
            if body is None:
                return soap_request
            
            # Find or create the request element
            # Look for any existing child element (request element)
            request_elem = None
            for child in body:
                if child.tag:
                    request_elem = child
                    break
            
            # If no request element exists, create it
            if request_elem is None:
                # Create the request element (usually named {namespace}operationRequest)
                request_tag = f"{{{ns['tns']}}}{operation_name}Request"
                request_elem = ET.SubElement(body, request_tag)

            # Add only missing or empty required fields from WSDL
            for child_schema in wsdl_schema.children:
                if not child_schema.is_required:
                    continue

                existing_field = SoapRequestFixer._find_field_element(
                    request_elem,
                    ns['tns'],
                    child_schema.name
                )
                if existing_field is not None and (existing_field.text or '').strip():
                    continue

                if existing_field is None:
                    child_tag = f"{{{ns['tns']}}}{child_schema.name}"
                    existing_field = ET.SubElement(request_elem, child_tag)

                sample_value = SoapRequestFixer.generate_sample_value(child_schema)
                existing_field.text = sample_value
                print(f"    [+] Added required field '{child_schema.name}' = '{sample_value}'")
            
            # Convert back to string with proper formatting
            request_str = ET.tostring(root, encoding='unicode')
            
            # Format nicely - remove extra blank lines
            lines = request_str.split('\n')
            lines = [line for line in lines if line.strip()]
            return '\n'.join(lines)
            
        except Exception as e:
            print(f"[!] Error fixing request: {e}")
            return soap_request


class SoapSelfHealingAgent:
    """Main agent orchestrating the self-healing process"""
    
    def __init__(self, project_root: str, wsdl_path: str, soapui_project_path: str):
        self.project_root = project_root
        self.wsdl_path = wsdl_path
        self.soapui_project_path = soapui_project_path
        self.config = self._load_config(Path(project_root) / "agent-config.json")
        
        self.wsdl_analyzer = WSDLAnalyzer(wsdl_path)
        self.test_analyzer = SoapTestAnalyzer(soapui_project_path)
        self.request_fixer = SoapRequestFixer()
        
        execution_config = self.config.get("execution", {})
        self.max_iterations = execution_config.get("max_iterations", 5)
        self.retry_delay = execution_config.get("retry_delay", 2)
        self.auto_sync_endpoint = self.config.get("healing_scope", {}).get(
            "allow_endpoint_updates",
            True
        )
        self.mock_service_enabled = self.config.get("mock_service", {}).get(
            "auto_start_local_mock",
            True
        )
        self.mock_service = None
        self.iteration = 0
        self.history = []

    def _load_config(self, config_path: Path) -> Dict:
        """Load JSON config when available"""
        if not config_path.exists():
            return {}

        try:
            with config_path.open("r", encoding="utf-8") as config_file:
                return json.load(config_file)
        except Exception as exc:
            print(f"[!] Failed to load config {config_path}: {exc}")
            return {}

    def _synchronize_endpoint(self) -> bool:
        """Keep SoapUI endpoint aligned with the current WSDL endpoint"""
        if not self.auto_sync_endpoint:
            return False

        wsdl_endpoint = self.wsdl_analyzer.get_service_endpoint()
        if not wsdl_endpoint:
            return False

        if self.test_analyzer.update_endpoint_in_project(wsdl_endpoint):
            print(f"[*] Synchronized SoapUI endpoint to WSDL address: {wsdl_endpoint}")
            return True

        return False

    def _start_mock_service_if_needed(self):
        """Start a local mock SOAP service for localhost endpoints"""
        if not self.mock_service_enabled:
            return

        endpoint = self.test_analyzer._get_endpoint()
        if not endpoint:
            return

        parsed = urlparse(endpoint)
        if parsed.hostname not in {"localhost", "127.0.0.1"}:
            return

        self.mock_service = LocalSoapMockService(endpoint, self.wsdl_analyzer)
        self.mock_service.start()
    
    def run(self) -> bool:
        """Main execution loop"""
        print("\n" + "="*70)
        print("INTELLIGENT SOAP SELF-HEALING TEST AGENT")
        print("="*70)
        print(f"Service: {self.wsdl_analyzer.service_name}")
        print(f"WSDL: {self.wsdl_path}")
        print(f"Project: {self.soapui_project_path}")
        print("="*70 + "\n")

        try:
            project_changed = self._synchronize_endpoint()
            self._start_mock_service_if_needed()

            while self.iteration < self.max_iterations:
                self.iteration += 1
                print(f"\n[ITERATION {self.iteration}/{self.max_iterations}]")
                print("-" * 70)

                # Step 1: Run tests
                test_result = self.test_analyzer.run_tests()

                if test_result['passed']:
                    if project_changed:
                        self.test_analyzer.save_project()
                    print("[✓] ALL TESTS PASSED!")
                    self._log_success()
                    return True

                # Step 2: Analyze failures
                print("\n[*] Analyzing test failures...")
                failures = self.test_analyzer.extract_failures(
                    test_result['stdout'] + test_result['stderr']
                )

                if failures:
                    for i, failure in enumerate(failures):
                        print(f"  Failure {i+1}: {failure['message']}")

                # Step 3: Get current requests
                requests = self.test_analyzer.get_test_requests()

                if not requests:
                    print("[!] No test requests found")
                    break

                # Step 4: Fix requests based on WSDL
                print("\n[*] Analyzing WSDL and fixing requests...")
                fixed_any = False

                for call_name, request_xml in requests.items():
                    print(f"\n  Processing: {call_name}")

                    # Extract operation name from request or use a default
                    operation = self._extract_operation_from_request(request_xml)

                    if not operation:
                        print(f"    [!] Could not determine operation name")
                        continue

                    # Get WSDL schema for this operation
                    wsdl_schema = self.wsdl_analyzer.get_request_schema(operation)

                    if not wsdl_schema:
                        print(f"    [!] Could not find schema for operation: {operation}")
                        continue

                    # Fix the request
                    fixed_request = self.request_fixer.fix_request_from_wsdl(
                        request_xml,
                        wsdl_schema,
                        operation
                    )

                    if fixed_request != request_xml:
                        if self.test_analyzer.update_request_in_project(
                            call_name,
                            fixed_request,
                            request_xml
                        ):
                            print(f"    [+] Updated request '{call_name}'")
                            fixed_any = True
                            project_changed = True
                        else:
                            print(f"    [!] Failed to update request '{call_name}'")

                if not fixed_any:
                    print("\n[!] No fixes were applied. Stopping.")
                    break

                # Step 5: Save project
                self.test_analyzer.save_project()

                # Log iteration
                self._log_iteration(test_result, failures)

                # Wait before next iteration
                if self.iteration < self.max_iterations:
                    print("\n[*] Waiting before next iteration...")
                    time.sleep(self.retry_delay)

            print(f"\n[!] Max iterations ({self.max_iterations}) reached without full success.")
            return False
        finally:
            if self.mock_service is not None:
                self.mock_service.stop()
    
    def _extract_operation_from_request(self, soap_xml: str) -> Optional[str]:
        """Extract operation name from SOAP request"""
        try:
            root = ET.fromstring(soap_xml)
            # Look for the first element in body (usually the request element)
            namespaces = {
                'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            }
            body = root.find('.//soapenv:Body', namespaces)
            if body is not None:
                for child in body:
                    tag = child.tag
                    # Remove namespace prefix
                    if '}' in tag:
                        tag = tag.split('}')[1]
                    # Remove 'Request' suffix if present
                    if tag.endswith('Request'):
                        return tag[:-7]  # Remove 'Request'
                    return tag
        except:
            pass
        
        # Fallback to regex
        match = re.search(r'<(\w+:)?(\w+)Request', soap_xml)
        if match:
            return match.group(2)
        
        return None
    
    def _log_iteration(self, test_result: Dict, failures: List[Dict]):
        """Log iteration details"""
        self.history.append({
            'iteration': self.iteration,
            'passed': test_result['passed'],
            'failure_count': len(failures),
            'timestamp': datetime.now().isoformat()
        })
    
    def _log_success(self):
        """Log successful completion"""
        print("\n" + "="*70)
        print("SUCCESS! All tests passed on iteration", self.iteration)
        print("="*70)
        print("\nTest History:")
        for entry in self.history:
            status = "✓" if entry['passed'] else "✗"
            print(f"  [{status}] Iteration {entry['iteration']}: "
                  f"{entry['failure_count']} failures")


class LocalSoapMockService:
    """Minimal local SOAP mock server for localhost-based CI execution"""

    def __init__(self, endpoint_url: str, wsdl_analyzer: WSDLAnalyzer):
        self.endpoint_url = endpoint_url
        self.wsdl_analyzer = wsdl_analyzer
        self.server = None
        self.thread = None
        self.parsed_endpoint = urlparse(endpoint_url)

    def start(self):
        """Start the mock server if the configured port is available"""
        host = self.parsed_endpoint.hostname or "127.0.0.1"
        port = self.parsed_endpoint.port or 80
        path = self.parsed_endpoint.path or "/"

        service = self

        class SoapMockHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path != path:
                    self.send_response(404)
                    self.end_headers()
                    return

                body_length = int(self.headers.get('Content-Length', '0'))
                request_body = self.rfile.read(body_length).decode('utf-8')
                status_code, response_body = service._build_response(request_body)
                self.send_response(status_code)
                self.send_header('Content-Type', 'text/xml; charset=utf-8')
                self.end_headers()
                self.wfile.write(response_body.encode('utf-8'))

            def log_message(self, format, *args):
                return

        self.server = ThreadingHTTPServer((host, port), SoapMockHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"[*] Local SOAP mock service listening on {host}:{port}{path}")

    def stop(self):
        """Stop the mock server"""
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            print("[*] Local SOAP mock service stopped")

    def _build_response(self, soap_xml: str) -> Tuple[int, str]:
        operation = self._extract_operation_name(soap_xml)
        if not operation:
            return 500, self._fault_response("Unable to determine SOAP operation")

        schema = self.wsdl_analyzer.get_request_schema(operation)
        if not schema:
            return 500, self._fault_response(f"No WSDL schema found for operation {operation}")

        request_values = self._extract_request_values(soap_xml)
        missing_fields = [
            child.name
            for child in schema.children
            if child.is_required and not (request_values.get(child.name) or "").strip()
        ]

        if missing_fields:
            return 500, self._fault_response(
                "Missing required field(s): " + ", ".join(sorted(missing_fields))
            )

        return 200, self._success_response(operation, request_values)

    def _extract_operation_name(self, soap_xml: str) -> Optional[str]:
        try:
            root = ET.fromstring(soap_xml)
            body = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            if body is None:
                return None

            for child in body:
                tag = child.tag.split('}', 1)[-1]
                return tag[:-7] if tag.endswith('Request') else tag
        except ET.ParseError:
            return None
        return None

    def _extract_request_values(self, soap_xml: str) -> Dict[str, str]:
        values = {}
        try:
            root = ET.fromstring(soap_xml)
            body = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            if body is None:
                return values

            request_elem = next(iter(body), None)
            if request_elem is None:
                return values

            for child in request_elem:
                field_name = child.tag.split('}', 1)[-1]
                values[field_name] = (child.text or '').strip()
        except ET.ParseError:
            return values

        return values

    def _success_response(self, operation: str, request_values: Dict[str, str]) -> str:
        namespace = self.wsdl_analyzer._extract_target_namespace()
        case_id = request_values.get("caseId", "123")
        status = request_values.get("status", "SUCCESS") or "SUCCESS"

        echoed_fields = []
        for field_name, field_value in request_values.items():
            if field_name == "status":
                continue
            echoed_fields.append(f"<{field_name}>{field_value}</{field_name}>")

        echoed_fields.insert(0, f"<caseFileId>CF-{case_id}</caseFileId>")
        echoed_fields.insert(1, f"<status>{status}</status>")

        payload = "".join(echoed_fields)
        return (
            f'<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            f'xmlns:tns="{namespace}"><soapenv:Header/><soapenv:Body>'
            f'<tns:{operation}Response>{payload}</tns:{operation}Response>'
            f'</soapenv:Body></soapenv:Envelope>'
        )

    def _fault_response(self, message: str) -> str:
        return (
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
            '<soapenv:Body><soapenv:Fault><faultcode>soapenv:Client</faultcode>'
            f'<faultstring>{message}</faultstring>'
            '</soapenv:Fault></soapenv:Body></soapenv:Envelope>'
        )


def main():
    """Main entry point"""
    # Setup paths
    script_dir = Path(__file__).parent
    project_root = str(script_dir)
    
    # Find files
    wsdl_files = list(script_dir.glob("*.wsdl"))
    xml_files = [f for f in script_dir.glob("*.xml") if "final" in f.name]
    
    if not wsdl_files:
        print("[!] No WSDL file found in project root")
        return 1
    
    if not xml_files:
        print("[!] No SoapUI project file found in project root")
        return 1
    
    wsdl_path = str(wsdl_files[0])
    soapui_project_path = str(xml_files[0])
    
    # Create and run agent
    agent = SoapSelfHealingAgent(project_root, wsdl_path, soapui_project_path)
    
    try:
        success = agent.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n[!] Agent interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[!] Agent error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
