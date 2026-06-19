#!/usr/bin/env python3
"""
Extract error queries from db.log and rerun them individually
"""
import re
import sys
import time
from pathlib import Path
from evaluation.script.evaluating.util import (
    execute_query,
    file_handler,
    get_mdb_server_memory,
    kill_server,
    send_query,
    start_server,
    write_json,
)
from evaluation.script.evaluating.option import DBS_DIR, ROOT_TEST_DIR

def extract_error_queries(log_path):
    """Extract node IDs and queries that had exceptions from db.log"""
    with open(log_path, 'r') as f:
        content = f.read()
    
    # Pattern to match query blocks
    query_pattern = r'Query\(worker (\d+),.*?\)Match \(N(\d+)\) =\[(.*?)\]\s*Return'
    exception_pattern = r'Unexpected\(\d+\) exception: expression is not a string literal'
    
    queries = []
    error_queries = []
    
    # Split by Query( to get individual query blocks
    blocks = re.split(r'(?=Query\(worker)', content)
    
    for block in blocks:
        if not block.strip():
            continue
            
        # Extract query info
        match = re.search(r'Query\(worker (\d+).*?\)Match \(N(\d+)\) =\[(.*?)\]\s*Return', block, re.DOTALL)
        if not match:
            continue
            
        worker_id, node_id, query_expr = match.groups()
        
        # Check if this block has an exception
        has_exception = bool(re.search(exception_pattern, block))
        
        full_query = f"Match (N{node_id}) =[{query_expr}] Return * Limit 1"
        
        entry = {
            'node_id': int(node_id),
            'worker': int(worker_id),
            'query': full_query,
            'has_error': has_exception
        }
        queries.append(entry)
        
        if has_exception:
            error_queries.append(entry)
    
    return queries, error_queries

def rerun_error_queries(error_queries):
    """Rerun only the queries that had errors"""
    print(f"\n{'='*80}")
    print(f"RERUNNING {len(error_queries)} ERROR QUERIES")
    print(f"{'='*80}\n")
    
    results = []
    successes = 0
    failures = 0
    
    server = start_server(DBS_DIR / "telecom")
    time.sleep(1)
    
    for idx, entry in enumerate(error_queries):
        node_id = entry['node_id']
        query = entry['query']
        
        sys.stdout.write(f"\r[{idx+1}/{len(error_queries)}] Testing node N{node_id}...")
        sys.stdout.flush()
        
        try:
            start_time = time.time_ns()
            result = send_query(query)
            end_time = time.time_ns()
            elapsed_ms = (end_time - start_time) / 1000000
            
            # Check if result contains error indication
            if "Unexpected" in result or "exception" in result.lower():
                failures += 1
                status = "FAILED"
                result_text = result[:100]
            else:
                successes += 1
                status = "SUCCESS"
                result_text = f"Results: {len(result.split()) if result else 0} tokens"
            
            results.append({
                'node_id': node_id,
                'status': status,
                'time_ms': elapsed_ms,
                'result': result_text
            })
        except Exception as e:
            failures += 1
            results.append({
                'node_id': node_id,
                'status': 'ERROR',
                'time_ms': 0,
                'result': str(e)[:100]
            })
    
    kill_server(server)
    
    # Print results
    print(f"\n\n{'='*80}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*80}")
    print(f"Total error queries:  {len(error_queries)}")
    print(f"Rerun successes:      {successes}")
    print(f"Rerun failures:       {failures}")
    print(f"{'='*80}\n")
    
    # Print detailed results
    print(f"{'Node ID':<15} {'Status':<12} {'Time (ms)':<12} {'Result':<50}")
    print("-" * 89)
    for r in results:
        status = r['status']
        time_str = f"{r['time_ms']:.2f}" if r['time_ms'] > 0 else "N/A"
        result_text = r['result'].replace('\n', ' ')[:50]
        print(f"N{r['node_id']:<14} {status:<12} {time_str:<12} {result_text:<50}")
    
    # Save results to file
    output_file = Path("/tmp/error_query_rerun_results.txt")
    with open(output_file, 'w') as f:
        f.write(f"Error Query Rerun Results\n")
        f.write(f"{'='*80}\n")
        f.write(f"Total error queries:  {len(error_queries)}\n")
        f.write(f"Rerun successes:      {successes}\n")
        f.write(f"Rerun failures:       {failures}\n")
        f.write(f"{'='*80}\n\n")
        
        for r in results:
            f.write(f"Node N{r['node_id']}: {r['status']}\n")
            f.write(f"  Time: {r['time_ms']:.2f}ms\n")
            f.write(f"  Result: {r['result']}\n\n")
    
    print(f"\nDetailed results saved to: {output_file}")
    return results

if __name__ == '__main__':
    log_path = Path("/home/heyang-li/research/MillenniumDB/evaluation/case-study/telecom/optimized/Q4/data-4/db.log")
    
    if not log_path.exists():
        print(f"Error: Log file not found: {log_path}")
        sys.exit(1)
    
    print("Extracting error queries from db.log...")
    all_queries, error_queries = extract_error_queries(log_path)
    
    print(f"Found {len(all_queries)} total queries")
    print(f"Found {len(error_queries)} error queries")
    
    if error_queries:
        print(f"\nFirst few error node IDs: {[q['node_id'] for q in error_queries[:5]]}")
        rerun_error_queries(error_queries)
    else:
        print("\nNo error queries found!")
