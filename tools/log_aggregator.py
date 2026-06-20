"""
Log aggregator tool with regex-based parser and production-validated test suite.
"""
import re
import sys
from typing import Dict, List, Optional


class LogParser:
    """Parses structured log lines using regex patterns."""
    
    # Pattern for standard log format: [TIMESTAMP] LEVEL MODULE: MESSAGE
    LOG_PATTERN = re.compile(
        r'^\[(?P<timestamp>[^\]]+)\]\s+(?P<level>\w+)\s+(?P<module>[\w\.]+):\s+(?P<message>.*)$'
    )
    
    # Pattern for optional key=value pairs in message
    KV_PATTERN = re.compile(r'(\w+)=([^\s]+)')
    
    def parse_line(self, line: str) -> Optional[Dict[str, str]]:
        """Parse a single log line into structured fields."""
        line = line.strip()
        if not line:
            return None
            
        match = self.LOG_PATTERN.match(line)
        if not match:
            return None
            
        result = match.groupdict()
        
        # Extract key-value pairs from message if present
        kv_matches = self.KV_PATTERN.findall(result['message'])
        if kv_matches:
            result['metadata'] = dict(kv_matches)
            
        return result
    
    def parse_logs(self, lines: List[str]) -> List[Dict[str, str]]:
        """Parse multiple log lines."""
        return [parsed for line in lines if (parsed := self.parse_line(line)) is not None]


def aggregate_logs(log_file: str) -> Dict[str, int]:
    """Aggregate logs by level from a log file."""
    parser = LogParser()
    aggregation = {}
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Log file '{log_file}' not found")
        return aggregation
    
    parsed_logs = parser.parse_logs(lines)
    
    for log in parsed_logs:
        level = log.get('level', 'UNKNOWN')
        aggregation[level] = aggregation.get(level, 0) + 1
    
    return aggregation


# Test Suite with Production-Based Data
class TestLogParser:
    """Test suite using anonymized production log samples."""
    
    @staticmethod
    def run_tests():
        """Run all test cases."""
        parser = LogParser()
        passed = 0
        failed = 0
        
        # Test 1: Standard production log format
        test_cases = [
            {
                'name': 'Valid standard log',
                'input': '[2024-01-15 10:23:45] INFO app.core: User authentication successful user_id=12345 session=abc123',
                'expected': {
                    'timestamp': '2024-01-15 10:23:45',
                    'level': 'INFO',
                    'module': 'app.core',
                    'message': 'User authentication successful user_id=12345 session=abc123',
                    'metadata': {'user_id': '12345', 'session': 'abc123'}
                }
            },
            {
                'name': 'ERROR level log',
                'input': '[2024-01-15 10:24:01] ERROR database.connector: Connection timeout host=db01.internal port=5432',
                'expected': {
                    'timestamp': '2024-01-15 10:24:01',
                    'level': 'ERROR',
                    'module': 'database.connector',
                    'message': 'Connection timeout host=db01.internal port=5432',
                    'metadata': {'host': 'db01.internal', 'port': '5432'}
                }
            },
            {
                'name': 'WARNING with complex module path',
                'input': '[2024-01-15 10:25:33] WARNING security.auth.validator: Rate limit approaching threshold=95%',
                'expected': {
                    'timestamp': '2024-01-15 10:25:33',
                    'level': 'WARNING',
                    'module': 'security.auth.validator',
                    'message': 'Rate limit approaching threshold=95%',
                    'metadata': {'threshold': '95%'}
                }
            },
            # Edge Case 1: Malformed timestamp (missing closing bracket)
            {
                'name': 'Edge case: Missing closing bracket in timestamp',
                'input': '[2024-01-15 10:26:00 ERROR app.core: Malformed log entry',
                'expected': None
            },
            # Edge Case 2: Missing log level
            {
                'name': 'Edge case: Missing log level',
                'input': '[2024-01-15 10:26:15] app.core: Missing level field',
                'expected': None
            },
            # Edge Case 3: Empty/whitespace only line
            {
                'name': 'Edge case: Empty line',
                'input': '   ',
                'expected': None
            },
            # Edge Case 4: Log with no metadata
            {
                'name': 'Simple log without metadata',
                'input': '[2024-01-15 10:27:00] DEBUG network.handler: Connection established',
                'expected': {
                    'timestamp': '2024-01-15 10:27:00',
                    'level': 'DEBUG',
                    'module': 'network.handler',
                    'message': 'Connection established'
                }
            },
            # Edge Case 5: Timestamp with milliseconds
            {
                'name': 'Timestamp with milliseconds',
                'input': '[2024-01-15 10:28:45.123] INFO cache.redis: Cache hit key=user:profile:789',
                'expected': {
                    'timestamp': '2024-01-15 10:28:45.123',
                    'level': 'INFO',
                    'module': 'cache.redis',
                    'message': 'Cache hit key=user:profile:789',
                    'metadata': {'key': 'user:profile:789'}
                }
            },
            # Edge Case 6: Message with special characters
            {
                'name': 'Message with special characters',
                'input': '[2024-01-15 10:29:00] ERROR api.handler: Request failed: 404 Not Found',
                'expected': {
                    'timestamp': '2024-01-15 10:29:00',
                    'level': 'ERROR',
                    'module': 'api.handler',
                    'message': 'Request failed: 404 Not Found'
                }
            }
        ]
        
        for test in test_cases:
            result = parser.parse_line(test['input'])
            
            if result == test['expected']:
                print(f"✓ PASS: {test['name']}")
                passed += 1
            else:
                print(f"✗ FAIL: {test['name']}")
                print(f"  Expected: {test['expected']}")
                print(f"  Got: {result}")
                failed += 1
        
        # Test batch parsing
        batch_input = [
            '[2024-01-15 11:00:00] INFO batch.processor: Starting batch job=daily_report',
            '',
            '[2024-01-15 11:00:05] INFO batch.processor: Processing records count=1000',
            'Invalid log line without proper format',
            '[2024-01-15 11:00:10] INFO batch.processor: Batch complete status=success'
        ]
        
        batch_result = parser.parse_logs(batch_input)
        if len(batch_result) == 3:
            print("✓ PASS: Batch parsing filters invalid lines")
            passed += 1
        else:
            print(f"✗ FAIL: Batch parsing - expected 3 valid logs, got {len(batch_result)}")
            failed += 1
        
        print(f"\n{'='*50}")
        print(f"Test Results: {passed} passed, {failed} failed")
        print(f"Pass rate: {(passed/(passed+failed)*100):.1f}%")
        print(f"{'='*50}")
        
        return failed == 0


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        success = TestLogParser.run_tests()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 1:
        result = aggregate_logs(sys.argv[1])
        print("Log Aggregation Results:")
        for level, count in sorted(result.items()):
            print(f"  {level}: {count}")
    else:
        print("Usage: python log_aggregator.py [test|<log_file>]")
        sys.exit(1)