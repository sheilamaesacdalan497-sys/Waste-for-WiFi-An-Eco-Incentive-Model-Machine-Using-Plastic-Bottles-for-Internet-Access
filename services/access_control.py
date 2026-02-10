"""Access control abstraction with optional iptables backend.

The `AccessController` class delegates to an implementation chosen at
initialization time. On a Pi you can enable iptables rules by setting
`USE_IPTABLES=True` in app config; set `DRY_RUN=True` to avoid actually
running system commands during testing.
"""
import logging
import subprocess
from threading import Lock
from typing import Optional


class _InMemoryController:
	def __init__(self, app=None):
		self._allowed = set()
		self._lock = Lock()

	def grant(self, ip: str, duration_seconds: int):
		with self._lock:
			self._allowed.add(ip)
		logging.info("InMemoryController.grant %s for %s seconds", ip, duration_seconds)
		return True

	def revoke(self, ip: str):
		with self._lock:
			self._allowed.discard(ip)
		logging.info("InMemoryController.revoke %s", ip)
		return True

	def is_allowed(self, ip: str) -> bool:
		with self._lock:
			return ip in self._allowed

	def list_allowed(self):
		with self._lock:
			return list(self._allowed)


class _IptablesController:
	def __init__(self, app=None, dry_run=True):
		self._lock = Lock()
		self._allowed = set()
		self.dry_run = bool(dry_run)

	def _run(self, cmd):
		logging.debug("Iptables cmd: %s (dry_run=%s)", " ".join(cmd), self.dry_run)
		if self.dry_run:
			return 0
		return subprocess.check_call(cmd)

	def grant(self, ip: str, duration_seconds: int):
		# Insert a rule to allow forwarding for this source IP.
		cmd = ["iptables", "-I", "FORWARD", "-s", ip, "-j", "ACCEPT"]
		try:
			self._run(cmd)
			with self._lock:
				self._allowed.add(ip)
			logging.info("IptablesController.grant %s", ip)
			return True
		except Exception:
			logging.exception("Failed to grant iptables rule for %s", ip)
			return False

	def revoke(self, ip: str):
		cmd = ["iptables", "-D", "FORWARD", "-s", ip, "-j", "ACCEPT"]
		try:
			self._run(cmd)
			with self._lock:
				self._allowed.discard(ip)
			logging.info("IptablesController.revoke %s", ip)
			return True
		except Exception:
			logging.exception("Failed to revoke iptables rule for %s", ip)
			return False

	def is_allowed(self, ip: str) -> bool:
		with self._lock:
			return ip in self._allowed

	def list_allowed(self):
		with self._lock:
			return list(self._allowed)


class AccessController:
	def __init__(self, app=None):
		self.app = app
		use_iptables = False
		dry_run = True
		if app is not None:
			use_iptables = bool(app.config.get("USE_IPTABLES", False))
			dry_run = bool(app.config.get("DRY_RUN", True))

		if use_iptables:
			self._impl = _IptablesController(app=app, dry_run=dry_run)
			logging.info("AccessController using IptablesController (dry_run=%s)", dry_run)
		else:
			self._impl = _InMemoryController(app=app)
			logging.info("AccessController using InMemoryController")

	def grant(self, ip: str, duration_seconds: int):
		return self._impl.grant(ip, duration_seconds)

	def revoke(self, ip: str):
		return self._impl.revoke(ip)

	def is_allowed(self, ip: str) -> bool:
		return self._impl.is_allowed(ip)

	def list_allowed(self):
		return self._impl.list_allowed()
