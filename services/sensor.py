"""Sensor abstraction.

Provides a mock sensor for local testing and a simple interface for real sensors.
"""
import threading
import logging


class SensorInterface:
	def __init__(self, app=None):
		self.app = app

	def start(self):
		raise NotImplementedError()


class MockSensor(SensorInterface):
	"""A mock sensor that can be triggered programmatically.

	For demo/testing call `trigger(session_id)` to simulate a bottle drop.
	"""

	def __init__(self, app=None):
		super().__init__(app)
		self._callbacks = []

	def on_trigger(self, cb):
		self._callbacks.append(cb)

	def trigger(self, session_id=None):
		logging.info("MockSensor.trigger for %s", session_id)
		for cb in list(self._callbacks):
			try:
				cb(session_id)
			except Exception:
				logging.exception("sensor callback error")

	def start(self):
		# nothing to run for mock
		return
