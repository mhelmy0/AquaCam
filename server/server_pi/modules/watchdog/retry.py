"""
Retry watchdog with exponential backoff and jitter.

Wraps the RTMP pusher in a retry loop that handles failures gracefully
and reconnects with increasing delays.
"""

import time
import random
from typing import List, Callable


class RetryWatchdog:
    """
    Manages retry logic with backoff and jitter.

    Uses a predefined backoff schedule with random jitter to avoid
    thundering herd problems when multiple streamers reconnect.
    """

    def __init__(self, backoff_schedule: List[int], logger) -> None:
        """
        Initialize retry watchdog.

        Args:
            backoff_schedule: List of backoff delays in seconds.
            logger: JSON logger instance.
        """
        self.backoff_schedule = backoff_schedule
        self.logger = logger
        self.attempt = 0

    def get_next_delay(self) -> float:
        """
        Calculate next retry delay with jitter.

        Returns:
            Delay in seconds with ±10% jitter.
        """
        # Use the last value if we've exhausted the schedule
        if self.attempt < len(self.backoff_schedule):
            base_delay = self.backoff_schedule[self.attempt]
        else:
            base_delay = self.backoff_schedule[-1]

        # Add ±10% jitter
        jitter = random.uniform(-0.1, 0.1)
        delay = base_delay * (1.0 + jitter)

        return max(0.1, delay)  # Ensure delay is positive

    def run(self, task: Callable[[], None]) -> None:
        """
        Run a task with retry logic.

        The task should raise an exception if it fails. The watchdog will
        catch the exception, log it, sleep according to backoff, and retry.

        Args:
            task: Callable that performs the work (e.g., start and monitor pusher).
        """
        while True:
            try:
                self.logger.log("info", "watchdog", "task_start", {
                    "attempt": self.attempt
                }, f"Starting task (attempt {self.attempt})")

                # Run the task (blocks until failure)
                task()

                # If task completes without exception, reset attempt counter
                self.logger.log("info", "watchdog", "task_success", {}, "Task completed successfully")
                self.attempt = 0

            except Exception as e:
                delay = self.get_next_delay()

                self.logger.log("error", "watchdog", "task_failed", {
                    "attempt": self.attempt,
                    "error": str(e),
                    "next_retry_s": delay
                }, f"Task failed, retrying in {delay:.1f}s: {e}")

                self.attempt += 1
                time.sleep(delay)
