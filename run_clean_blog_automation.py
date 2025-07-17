#!/usr/bin/env python3
"""
Simple runner for the clean blog automation workflow.
Usage: python run_clean_blog_automation.py [max_jobs] [--debug]
"""

import sys
import os
import argparse
from blog_automation_clean import CleanBlogAutomation

def main():
    """Run the clean blog automation with optional parameters."""
    parser = argparse.ArgumentParser(description="Clean Blog Automation Runner")
    parser.add_argument(
        'max_jobs', 
        type=int, 
        nargs='?', 
        default=5,
        help='Maximum number of jobs to process (default: 5)'
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug mode with console logging'
    )
    
    args = parser.parse_args()
    
    # Print startup message
    if args.debug:
        print(f"🚀 Starting Clean Blog Automation (DEBUG MODE - max {args.max_jobs} jobs)")
    else:
        print(f"🚀 Starting Clean Blog Automation (max {args.max_jobs} jobs)")
        print("💡 Use --debug flag to see console logs")
    
    print("=" * 60)
    
    # Create automation instance with debug flag
    automation = CleanBlogAutomation(debug=args.debug)
    automation.run_automation(args.max_jobs)

if __name__ == "__main__":
    main()
