#!/usr/bin/env python3
"""
Main entry point for the blog-AI automation system.
"""

import sys
import os
import argparse

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from src.automation.content_automation import main as run_automation
from src.automation.manage_keywords import main as manage_keywords


def main():
    """Main CLI interface for the blog-AI system"""
    parser = argparse.ArgumentParser(description="Blog-AI Content Automation System")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Automation command
    automation_parser = subparsers.add_parser('automate', help='Run content automation')
    
    # Keywords management command
    keywords_parser = subparsers.add_parser('keywords', help='Manage semantic keywords')
    keywords_parser.add_argument("action", choices=["list", "preview", "update", "batch"], 
                               help="Action to perform")
    keywords_parser.add_argument("--job-id", type=int, help="Job ID for preview/update actions")
    keywords_parser.add_argument("--status", type=str, help="Filter jobs by status for batch action")
    keywords_parser.add_argument("--competitors", action="store_true", 
                               help="Include competitor keyword scraping")
    
    args = parser.parse_args()
    
    if args.command == 'automate':
        print("🚀 Running content automation...")
        run_automation()
    
    elif args.command == 'keywords':
        print("🔑 Managing semantic keywords...")
        # Set up sys.argv for the keywords script
        sys.argv = ['manage_keywords.py', args.action]
        if args.job_id:
            sys.argv.extend(['--job-id', str(args.job_id)])
        if args.status:
            sys.argv.extend(['--status', args.status])
        if args.competitors:
            sys.argv.append('--competitors')
        
        manage_keywords()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
