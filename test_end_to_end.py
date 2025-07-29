#!/usr/bin/env python3
"""
Simple End-to-End Test for TableTalk

Tests:
1. Application sanity (can it start and handle basic operations)
2. Natural language queries with actual LLM (iterates through test queries)
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import run_tabletalk_commands

# Test queries to validate LLM functionality
TEST_QUERIES = [
    "what files do we have",
    "show me the customers schema", 
    "describe the orders file",
    "find data quality issues",
    "detect type mismatches",
    "which files have customer_id",
    "compare schemas across files",
    "what data types are in customers file"
]

def run_tabletalk_with_input(commands, timeout=30):
    """Run TableTalk with given input commands using direct function calls."""
    try:
        results = run_tabletalk_commands(commands)
        
        # Convert results to simulate subprocess-like output
        stdout_lines = []
        stderr_lines = []
        returncode = 0
        
        for command, response, success in results:
            stdout_lines.append(f"TableTalk> {command}")
            if success:
                stdout_lines.append(response)
            else:
                stderr_lines.append(response)
                returncode = 1
        
        stdout = "\n".join(stdout_lines)
        stderr = "\n".join(stderr_lines)
        
        return stdout, stderr, returncode
        
    except Exception as e:
        return "", str(e), -1

def test_application_startup():
    """Test that the application can start and respond to basic commands."""
    print("🚀 Testing Application Startup...")
    
    stdout, stderr, returncode = run_tabletalk_with_input(["/help"], timeout=10)
    
    if "TableTalk" in stdout and returncode == 0:
        print("✅ Application startup successful")
        return True
    else:
        print("❌ Application startup failed")
        if stderr:
            print(f"   Error: {stderr[:100]}")
        return False

def test_file_scanning():
    """Test file scanning functionality."""
    print("\n📁 Testing File Scanning...")
    
    data_dir = Path(__file__).parent / "data" / "sample"
    
    commands = [f"/scan {data_dir}", "/status"]
    
    stdout, stderr, returncode = run_tabletalk_with_input(commands, timeout=15)
    
    if "files" in stdout.lower() and returncode == 0:
        print("✅ File scanning successful")
        # Count files mentioned in output
        file_count = stdout.lower().count(".csv")
        print(f"   Found references to {file_count} CSV files")
        return True
    else:
        print("❌ File scanning failed")
        if stderr:
            print(f"   Error: {stderr[:100]}")
        print(f"   Output: {stdout[:200]}")
        return False

def test_natural_language_queries():
    """Test natural language queries with actual LLM."""
    print("\n🤖 Testing Natural Language Queries...")
    print(f"📝 Running {len(TEST_QUERIES)} test queries")
    
    data_dir = Path(__file__).parent / "data" / "sample"
    successful = 0
    failed = 0
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n🔬 Query {i}/{len(TEST_QUERIES)}: \"{query}\"")
        
        # Each query gets fresh scan + query
        commands = [f"/scan {data_dir}", query]
        
        stdout, stderr, returncode = run_tabletalk_with_input(commands, timeout=30)
        
        # Check if we got a meaningful response
        if stdout and len(stdout) > 100 and returncode == 0:
            print("✅ SUCCESS")
            
            # Try to extract the response part (look for the query response)
            lines = stdout.split('\n')
            response_lines = []
            
            # Find lines after the query command
            query_found = False
            for line in lines:
                if query.lower() in line.lower() and "TableTalk>" in line:
                    query_found = True
                    continue
                elif query_found and line.strip() and not line.startswith("TableTalk>"):
                    response_lines.append(line.strip())
                elif query_found and line.startswith("TableTalk>"):
                    break
            response = " ".join(response_lines[:2])  # First couple lines
            print("*******")
            print(response_lines)
            print("*******")
            if response:
                print(f"📋 Response: {response[:120]}{'...' if len(response) > 120 else ''}")
            else:
                print("📋 Response: (generated successfully)")
                
            successful += 1
        else:
            print("❌ FAILED")
            if stderr:
                print(f"💥 Error: {stderr[:80]}")
            else:
                print("💥 No substantial response generated")
                print(f"💥 Output length: {len(stdout) if stdout else 0}")
            failed += 1
        
        # Small delay between queries
        time.sleep(0.5)
    
    return successful, failed

def main():
    """Run all tests."""
    print("🧪 TableTalk End-to-End Test Suite")
    print("=" * 50)
    
    # Check sample data exists
    data_dir = Path(__file__).parent / "data" / "sample"
    if not data_dir.exists():
        print(f"❌ Sample data directory not found: {data_dir}")
        return
    
    print(f"📁 Using sample data: {data_dir}")
    
    # Test 1: Basic application functionality
    startup_ok = test_application_startup()
    
    # Test 2: File scanning
    scanning_ok = test_file_scanning()
    
    # Test 3: Natural language queries (main test)
    if startup_ok and scanning_ok:
        successful_queries, failed_queries = test_natural_language_queries()
    else:
        print("\n⚠️ Skipping query tests due to startup/scanning failures")
        successful_queries = failed_queries = 0
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    print(f"🏗️ Infrastructure:")
    print(f"   Application Startup: {'✅' if startup_ok else '❌'}")
    print(f"   File Scanning: {'✅' if scanning_ok else '❌'}")
    
    total_queries = len(TEST_QUERIES)
    if total_queries > 0:
        success_rate = (successful_queries / total_queries) * 100
        print(f"\n🤖 Natural Language Queries:")
        print(f"   Successful: {successful_queries}/{total_queries}")
        print(f"   Failed: {failed_queries}/{total_queries}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\n🎯 Overall Assessment:")
        if startup_ok and scanning_ok and success_rate >= 70:
            print("   🎉 EXCELLENT - TableTalk working well!")
        elif startup_ok and scanning_ok and success_rate >= 50:
            print("   ✅ GOOD - Most functionality working")
        elif startup_ok and scanning_ok:
            print("   ⚠️ FAIR - Infrastructure OK, some query issues")
        else:
            print("   ❌ NEEDS ATTENTION - Basic functionality issues")
    
    print(f"\n💡 Notes:")
    print(f"   • Tests use direct function calls with real LLM integration")
    print(f"   • Each query runs independently with fresh file scan")
    print(f"   • Focus is on getting responses, not exact content")
    print(f"   • Run 'python -m src.main' manually for debugging")

if __name__ == "__main__":
    main()
