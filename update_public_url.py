#!/usr/bin/env python3
"""
Script to update PUBLIC_BASE_URL in .env file
Usage: python update_public_url.py https://your-new-url.com
"""
import sys
import os

def update_env_url(new_url):
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print("❌ .env file not found!")
        return False
    
    # Read current .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update PUBLIC_BASE_URL line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('PUBLIC_BASE_URL='):
            lines[i] = f'PUBLIC_BASE_URL={new_url}\n'
            updated = True
            break
    
    if not updated:
        # Add PUBLIC_BASE_URL if not found
        lines.append(f'PUBLIC_BASE_URL={new_url}\n')
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Updated PUBLIC_BASE_URL to: {new_url}")
    print("🔄 Please restart your Flask app to apply changes")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_public_url.py https://your-public-url")
        print("\nExamples:")
        print("  python update_public_url.py https://abc123.ngrok.io")
        print("  python update_public_url.py https://xyz.trycloudflare.com")
        sys.exit(1)
    
    new_url = sys.argv[1].strip()
    
    # Validate URL format
    if not (new_url.startswith('http://') or new_url.startswith('https://')):
        print("❌ URL must start with http:// or https://")
        sys.exit(1)
    
    update_env_url(new_url)
