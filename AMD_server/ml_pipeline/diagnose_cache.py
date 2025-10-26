#!/usr/bin/env python3
"""
Diagnostic script to check HuggingFace cache permissions
Safe to run - only checks, doesn't modify anything
"""

import os
import sys
from pathlib import Path

def check_permissions(path):
    """Check if path exists and is writable"""
    try:
        p = Path(path)
        exists = p.exists()
        if exists:
            # Check if readable
            readable = os.access(path, os.R_OK)
            # Check if writable
            writable = os.access(path, os.W_OK)
            # Check if executable (for directories)
            executable = os.access(path, os.X_OK)
            
            # Get detailed info
            stat_info = p.stat()
            owner = stat_info.st_uid
            permissions = oct(stat_info.st_mode)[-3:]
            
            return {
                'exists': True,
                'readable': readable,
                'writable': writable,
                'executable': executable,
                'owner_uid': owner,
                'permissions': permissions,
                'type': 'dir' if p.is_dir() else 'file'
            }
        else:
            return {'exists': False}
    except Exception as e:
        return {'exists': 'unknown', 'error': str(e)}

def main():
    print("=" * 70)
    print("HUGGINGFACE CACHE DIAGNOSTICS")
    print("=" * 70)
    
    # Get current user info
    import pwd
    current_user = pwd.getpwuid(os.getuid())
    print(f"\nCurrent user: {current_user.pw_name}")
    print(f"User ID: {os.getuid()}")
    print(f"Group ID: {os.getgid()}")
    
    # Check paths
    paths_to_check = [
        "/home/amd-knights",
        "/home/amd-knights/.cache",
        "/home/amd-knights/.cache/huggingface",
        "/home/amd-knights/.cache/huggingface/hub",
        "/home/amd-knights/.cache/huggingface/hub/.locks",
    ]
    
    print("\n" + "=" * 70)
    print("PATH PERMISSIONS CHECK")
    print("=" * 70)
    
    for path in paths_to_check:
        print(f"\n📁 {path}")
        info = check_permissions(path)
        
        if info.get('exists') == False:
            print(f"   ❌ Does not exist")
        elif info.get('exists') == 'unknown':
            print(f"   ⚠️  Error: {info.get('error')}")
        else:
            status = []
            if info['readable']:
                status.append("✅ Read")
            else:
                status.append("❌ Read")
            
            if info['writable']:
                status.append("✅ Write")
            else:
                status.append("❌ Write")
            
            if info['executable']:
                status.append("✅ Execute")
            else:
                status.append("❌ Execute")
            
            print(f"   {' | '.join(status)}")
            print(f"   Permissions: {info['permissions']} | Owner UID: {info['owner_uid']} | Type: {info['type']}")
    
    # Check for lock files
    print("\n" + "=" * 70)
    print("LOCK FILES CHECK")
    print("=" * 70)
    
    locks_dir = Path("/home/amd-knights/.cache/huggingface/hub/.locks")
    if locks_dir.exists():
        lock_files = list(locks_dir.glob("*"))
        if lock_files:
            print(f"\n⚠️  Found {len(lock_files)} lock file(s):")
            for lock in lock_files[:10]:  # Show first 10
                info = check_permissions(str(lock))
                print(f"\n   {lock.name}")
                print(f"   Owner UID: {info.get('owner_uid', 'unknown')}")
                print(f"   Permissions: {info.get('permissions', 'unknown')}")
        else:
            print("\n✅ No lock files found")
    else:
        print("\n📁 Lock directory doesn't exist yet")
    
    # Check HuggingFace cache environment variables
    print("\n" + "=" * 70)
    print("ENVIRONMENT VARIABLES")
    print("=" * 70)
    
    hf_vars = {
        'HF_HOME': os.environ.get('HF_HOME', 'Not set'),
        'HUGGINGFACE_HUB_CACHE': os.environ.get('HUGGINGFACE_HUB_CACHE', 'Not set'),
        'TRANSFORMERS_CACHE': os.environ.get('TRANSFORMERS_CACHE', 'Not set'),
        'HF_DATASETS_CACHE': os.environ.get('HF_DATASETS_CACHE', 'Not set'),
    }
    
    for var, value in hf_vars.items():
        print(f"   {var}: {value}")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    cache_info = check_permissions("/home/amd-knights/.cache/huggingface")
    
    if cache_info.get('exists') == False:
        print("\n✅ GOOD: Cache directory doesn't exist yet")
        print("   → Will be created automatically with correct permissions")
    elif not cache_info.get('writable'):
        print("\n❌ PROBLEM: Cache directory exists but not writable")
        print("   → Run: chmod -R u+w /home/amd-knights/.cache/huggingface")
    else:
        locks_dir = Path("/home/amd-knights/.cache/huggingface/hub/.locks")
        if locks_dir.exists():
            lock_files = list(locks_dir.glob("*"))
            if lock_files:
                print("\n⚠️  PROBLEM: Stale lock files found")
                print("   → Run: rm -rf /home/amd-knights/.cache/huggingface/hub/.locks/*")
            else:
                print("\n✅ GOOD: Cache directory is writable, no lock files")
        else:
            print("\n✅ GOOD: Cache directory is writable")
    
    print("\n" + "=" * 70)
    print("SAFE COMMANDS TO FIX (if needed)")
    print("=" * 70)
    print("""
# Option 1: Remove lock files (if they exist)
rm -rf /home/amd-knights/.cache/huggingface/hub/.locks/*

# Option 2: Fix permissions (if needed)
chmod -R u+w /home/amd-knights/.cache/huggingface

# Option 3: Start fresh (nuclear option - deletes all cached models)
# rm -rf /home/amd-knights/.cache/huggingface
# mkdir -p /home/amd-knights/.cache/huggingface

# Option 4: Use a different cache location
# export HF_HOME=/tmp/huggingface_cache_$USER
# mkdir -p $HF_HOME
""")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
