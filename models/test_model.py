
class MyTestModel:
    def __init__(self):
        self.tests = []

    def add_test(self, test_name):
        """Add a test to the model."""
        self.tests.append(test_name)

    def remove_test(self, test_name):
        """Remove a test from the model."""
        if test_name in self.tests:
            self.tests.remove(test_name)
