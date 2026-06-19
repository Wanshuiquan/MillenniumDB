#!/usr/bin/env python3
"""
Rerun all error queries from data-4 Q4
"""
import time
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, '/home/heyang-li/research/MillenniumDB')

from evaluation.script.evaluating.util import (
    send_query,
    start_server,
    kill_server,
)
from evaluation.script.evaluating.option import DBS_DIR

# Query template from telecom.py
Q44 = "DATA_TEST ?e (cell {?p == attr1 and ?q == attr2})/ (((:lived {true}) | (:used {true} ) | (:bought {true} ))/(user {?q - attr2 <= 0.1 and attr2 - ?q <= 0.1 and 0.5 * attr1 + 0.1 <= ?p}))*"

def test_error_queries():
    """Run all the error node IDs with the error query template"""
    
    # Read error node IDs
    with open('/tmp/error_node_ids.txt', 'r') as f:
        error_nodes = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(error_nodes)} error node IDs")
    print(f"First 5: {error_nodes[:5]}")
    print(f"\nStarting server and rerunning queries...")
    
    server = start_server(DBS_DIR / "telecom")
    time.sleep(2)
    
    results = []
    success_count = 0
    error_count = 0
    
    for idx, node_id in enumerate(error_nodes):
        sys.stdout.write(f"\r[{idx+1}/{len(error_nodes)}] Testing {node_id}...")
        sys.stdout.flush()
        
        # Create query command (must include => (?to) as per create_query_command format)
        query = f"Match ({node_id}) =[{Q44}] => (?to) \n Return * \n Limit 1"
        
        try:
            result = send_query(query)
            
            # Check for errors in result
            if "Unexpected" in result or "exception" in result.lower():
                error_count += 1
                status = "ERROR"
            else:
                success_count += 1
                status = "OK"
            
            results.append({
                'node': node_id,
                'status': status,
                'result': result[:80] if result else ""
            })
            
        except Exception as e:
            error_count += 1
            results.append({
                'node': node_id,
                'status': 'EXCEPTION',
                'result': str(e)[:80]
            })
    
    kill_server(server)
    
    # Summary
    print(f"\n\n{'='*80}")
    print(f"RERUN RESULTS")
    print(f"{'='*80}")
    print(f"Total error queries rerun:  {len(error_nodes)}")
    print(f"Queries that succeeded:     {success_count}")
    print(f"Queries that still failed:  {error_count}")
    print(f"{'='*80}\n")
    
    if success_count > 0:
        print(f"✓ {success_count} error queries now pass!")
    if error_count > 0:
        print(f"✗ {error_count} error queries still fail:")
        for r in results:
            if r['status'] != 'OK':
                print(f"  {r['node']}: {r['status']}")
    
    return success_count, error_count

if __name__ == '__main__':
    test_error_queries()
