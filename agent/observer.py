class Observer:
    """Observes the current page state. In the new architecture, observation is done directly in CoreAgent."""
    def __init__(self, browser_wrapper):
        self.browser = browser_wrapper
