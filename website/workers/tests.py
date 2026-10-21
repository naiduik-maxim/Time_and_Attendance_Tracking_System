from django.test import TestCase


class WorkerRoutesTests(TestCase):
    def test_general_hire_page_is_removed(self):
        self.assertEqual(self.client.get('/worker/hire/').status_code, 404)
