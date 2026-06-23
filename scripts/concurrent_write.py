#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Concurrent Write Protection (P2-10)
====================================
File locking mechanism for parallel sub-agent writes.

When multiple sub-agents write to shared files (e.g., unified_framework.md),
this module provides advisory file locking to prevent data corruption.

Usage:
  from concurrent_write import write_with_lock, read_with_lock

  # Write with lock
  write_with_lock("outputs/paper/unified_framework.md", content)

  # Read with lock (shared lock)
  content = read_with_lock("outputs/paper/unified_framework.md")

Design:
  - Uses platform-specific file locking (fcntl on Unix, msvcrt on Windows)
  - Advisory locking (cooperative — all writers must use this module)
  - Timeout after 30 seconds to prevent deadlocks
  - Graceful fallback if locking unavailable
"""

import os
import sys
import time
from pathlib import Path
from contextlib import contextmanager

# Platform-specific locking
_lock_available = True
try:
    if sys.platform == "win32":
        import msvcrt
        def _lock_file(f, exclusive=True):
            """Lock file on Windows using msvcrt."""
            mode = msvcrt.LK_NBLCK if exclusive else msvcrt.LK_LOCK
            try:
                msvcrt.locking(f.fileno(), mode, 1)
                return True
            except (IOError, OSError):
                return False

        def _unlock_file(f):
            """Unlock file on Windows."""
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            except (IOError, OSError):
                pass
    else:
        import fcntl
        def _lock_file(f, exclusive=True):
            """Lock file on Unix using fcntl."""
            flag = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            try:
                fcntl.flock(f.fileno(), flag | fcntl.LOCK_NB)
                return True
            except (IOError, OSError):
                return False

        def _unlock_file(f):
            """Unlock file on Unix."""
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except (IOError, OSError):
                pass

except ImportError:
    _lock_available = False
    def _lock_file(f, exclusive=True):
        return True  # No-op fallback

    def _unlock_file(f):
        pass


@contextmanager
def file_lock(filepath, exclusive=True, timeout=30, retry_interval=0.5):
    """Context manager for file locking.

    Args:
        filepath: Path to file to lock
        exclusive: True for exclusive (write) lock, False for shared (read) lock
        timeout: Maximum seconds to wait for lock
        retry_interval: Seconds between lock attempts

    Usage:
        with file_lock("outputs/paper/unified_framework.md"):
            content = Path("outputs/paper/unified_framework.md").read_text()
            # modify content
            Path("outputs/paper/unified_framework.md").write_text(content)
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if not _lock_available:
        yield  # No locking available, proceed without lock
        return

    # Create lock file alongside target
    lock_path = filepath.with_suffix(filepath.suffix + ".lock")
    start_time = time.time()
    locked = False

    try:
        f = open(lock_path, "w")
        while time.time() - start_time < timeout:
            if _lock_file(f, exclusive):
                locked = True
                # Write PID to lock file for debugging
                f.write(f"pid={os.getpid()}\n")
                f.flush()
                break
            time.sleep(retry_interval)

        if not locked:
            raise TimeoutError(
                f"Could not acquire {'exclusive' if exclusive else 'shared'} lock "
                f"on {filepath} within {timeout}s. "
                f"Another agent may be writing to this file."
            )

        yield  # Proceed with locked file

    finally:
        if locked:
            _unlock_file(f)
        f.close()
        # Clean up lock file
        try:
            lock_path.unlink(missing_ok=True)
        except Exception:
            pass


def write_with_lock(filepath, content, encoding="utf-8"):
    """Write content to file with exclusive lock.

    Args:
        filepath: Path to write to
        content: String content to write
        encoding: File encoding (default utf-8)
    """
    filepath = Path(filepath)
    with file_lock(filepath, exclusive=True):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding=encoding)


def read_with_lock(filepath, encoding="utf-8"):
    """Read content from file with shared lock.

    Args:
        filepath: Path to read from
        encoding: File encoding (default utf-8)

    Returns:
        File content as string, or empty string if file doesn't exist
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return ""
    with file_lock(filepath, exclusive=False):
        return filepath.read_text(encoding=encoding)


def append_with_lock(filepath, content, encoding="utf-8"):
    """Append content to file with exclusive lock.

    Args:
        filepath: Path to append to
        content: String content to append
        encoding: File encoding (default utf-8)
    """
    filepath = Path(filepath)
    with file_lock(filepath, exclusive=True):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "a", encoding=encoding) as f:
            f.write(content)


# CLI for testing
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Concurrent Write Protection Test")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("test-write", help="Test write with lock")
    sp.add_argument("filepath", help="File to write")
    sp.add_argument("content", help="Content to write")

    sp = sub.add_parser("test-read", help="Test read with lock")
    sp.add_argument("filepath", help="File to read")

    sp = sub.add_parser("test-append", help="Test append with lock")
    sp.add_argument("filepath", help="File to append to")
    sp.add_argument("content", help="Content to append")

    args = p.parse_args()

    if args.cmd == "test-write":
        write_with_lock(args.filepath, args.content)
        print(f"Written to {args.filepath}")
    elif args.cmd == "test-read":
        content = read_with_lock(args.filepath)
        print(content)
    elif args.cmd == "test-append":
        append_with_lock(args.filepath, args.content)
        print(f"Appended to {args.filepath}")
    else:
        p.print_help()
