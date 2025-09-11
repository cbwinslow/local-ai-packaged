#!/usr/bin/env python3
"""
API Key Registration Script
Helps register for API keys needed to access government data APIs.
"""

import webbrowser
import sys

def register_govinfo_api_key():
    """Open browser to register for govinfo API key."""
    print("Registering for govinfo API key...")
    print("This will open your browser to the api.data.gov registration page.")
    print("You'll need to:")
    print("1. Fill out the registration form")
    print("2. Verify your email address")
    print("3. Copy your API key from the dashboard")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        webbrowser.open("https://api.data.gov/signup/")
        print("Browser opened to api.data.gov signup page.")
        print("After registration, add your API key to your .env file as GOVINFO_API_KEY=your_key_here")
    else:
        print("Registration cancelled.")

def register_congress_api_key():
    """Open browser to register for congress.gov API key."""
    print("Registering for congress.gov API key...")
    print("This will open your browser to the congress.gov API key registration page.")
    print("You'll need to:")
    print("1. Create an account or log in")
    print("2. Navigate to the API section")
    print("3. Generate a new API key")
    print("4. Copy your API key")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        webbrowser.open("https://api.congress.gov/")
        print("Browser opened to congress.gov API page.")
        print("After registration, add your API key to your .env file as CONGRESS_API_KEY=your_key_here")
    else:
        print("Registration cancelled.")

def main():
    """Main function to register for API keys."""
    print("Government Data API Key Registration")
    print("====================================")
    print()
    print("This script helps you register for API keys needed to access government data.")
    print()
    
    while True:
        print("Select an API to register for:")
        print("1. GovInfo API (govinfo.gov)")
        print("2. Congress.gov API")
        print("3. Exit")
        print()
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            register_govinfo_api_key()
        elif choice == '2':
            register_congress_api_key()
        elif choice == '3':
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")
        
        print()
        input("Press Enter to continue...")
        print()

if __name__ == "__main__":
    main()