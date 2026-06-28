from __future__ import annotations

import os
import sys

from paths import PROFILES_DIR

LOCK_DIR = PROFILES_DIR / ".locks"


class AccountLock:
    def __init__(self, uid):
        self.uid = str(uid or "unknown")
        self._fh = None

    def acquire(self) -> bool:
        try:
            LOCK_DIR.mkdir(parents=True, exist_ok=True)
            fh = open(LOCK_DIR / f"{self.uid}.lock", "a+")
        except Exception:
            return True
        try:
            if sys.platform.startswith("win"):
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            return False
        try:
            fh.seek(0)
            fh.truncate()
            fh.write(str(os.getpid()))
            fh.flush()
        except Exception:
            pass
        self._fh = fh
        return True

    def release(self) -> None:
        if not self._fh:
            return
        try:
            if sys.platform.startswith("win"):
                import msvcrt
                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            self._fh.close()
        except Exception:
            pass
        self._fh = None


def acquire_accounts(profs) -> tuple[list, list, list]:
    locks, ok, skipped, seen = [], [], [], {}
    for p in profs:
        uid = getattr(p, "uid", "") or p.name
        if uid in seen:
            if seen[uid]:
                ok.append(p)
            else:
                skipped.append(p.name)
            continue
        lk = AccountLock(uid)
        got = lk.acquire()
        seen[uid] = got
        if got:
            locks.append(lk)
            ok.append(p)
        else:
            skipped.append(p.name)
    return ok, skipped, locks


def release_all(locks) -> None:
    for lk in locks or []:
        lk.release()
