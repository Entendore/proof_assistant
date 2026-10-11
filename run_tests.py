#!/usr/bin/env python3
"""
Test Runner for Interactive Proof Assistant
============================================

Run tests with various options:
    python run_tests.py                    # Run all tests
    python run_tests.py --single test_parser.py  # Run specific test file
    python run_tests.py -v                 # Verbose output
    python run_tests.py --coverage         # With coverage report
    python run_tests.py --pdb              # Drop into debugger on failure

"""

import sys
import pytest
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='Run proof assistant tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_tests.py                           # Run all tests
    python run_tests.py --single test_parser      # Run parser tests
    python run_tests.py -vv --coverage            # Verbose with coverage
    python run_tests.py tests/test_tactics.py     # Run specific file
        """
    )
    
    parser.add_argument(
        '--folder', 
        default='tests',
        help='Folder containing tests to run (default: tests)'
    )
    
    parser.add_argument(
        '--single', 
        help='Run only a specific test file or test function'
    )
    
    parser.add_argument(
        '--verbose', '-v', 
        action='count', 
        default=0,
        help='Increase verbosity (use -v, -vv, -vvv for more detail)'
    )
    
    parser.add_argument(
        '--pdb', 
        action='store_true',
        help='Drop into debugger on test failure'
    )
    
    parser.add_argument(
        '--coverage', 
        action='store_true',
        help='Generate coverage report'
    )
    
    parser.add_argument(
        '--html-cov',
        action='store_true',
        help='Generate HTML coverage report'
    )
    
    parser.add_argument(
        '-x', '--exitfirst',
        action='store_true',
        help='Exit on first failure'
    )
    
    parser.add_argument(
        '--lf', '--last-failed',
        action='store_true',
        help='Run only last failed tests'
    )
    
    parser.add_argument(
        '-k',
        help='Only run tests matching the given expression'
    )
    
    args = parser.parse_args()
    
    # Add project directory to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Prepare pytest arguments
    pytest_args = []
    
    # Set verbosity
    if args.verbose > 0:
        pytest_args.extend(['-' + 'v' * args.verbose])
    
    # Set debugger option
    if args.pdb:
        pytest_args.append('--pdb')
    
    # Set coverage option
    if args.coverage or args.html_cov:
        pytest_args.extend(['--cov=proof_assistant'])
        if args.html_cov:
            pytest_args.extend(['--cov-report=html:htmlcov'])
        pytest_args.extend(['--cov-report=term-missing'])
    
    # Exit on first failure
    if args.exitfirst:
        pytest_args.append('-x')
    
    # Last failed
    if args.last_failed:
        pytest_args.append('--lf')
    
    # Filter by expression
    if args.k:
        pytest_args.extend(['-k', args.k])
    
    # Determine which tests to run
    if args.single:
        if '::' in args.single:
            # It's a specific test function
            pytest_args.append(args.single)
        else:
            # It's a file
            test_path = Path(args.folder) / args.single
            if not test_path.exists():
                test_path = test_path.with_suffix('.py')
            
            if not test_path.exists():
                print(f"❌ Test file not found: {test_path}")
                return 1
            
            pytest_args.append(str(test_path))
    else:
        # Run all tests in the folder
        pytest_args.append(args.folder)
    
    # Print banner
    print("=" * 60)
    print("🧪 Interactive Proof Assistant - Test Suite")
    print("=" * 60)
    print(f"📁 Test folder: {args.folder}")
    print(f"🔧 Arguments: {' '.join(pytest_args)}")
    print("=" * 60)
    print()
    
    # Run the tests
    result = pytest.main(pytest_args)
    
    # Print summary
    print()
    print("=" * 60)
    if result == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed with exit code: {result}")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    sys.exit(main())
