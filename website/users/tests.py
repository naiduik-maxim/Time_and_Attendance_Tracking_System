import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ProfileFeedbackTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.user = get_user_model().objects.create_user(
            username='profile-test', email='before@example.com', password='test-pass-123',
        )
        self.client.force_login(self.user)

    def test_email_request_displays_notice_and_can_be_confirmed(self):
        response = self.client.post(reverse('profile'), {
            'action': 'email', 'email-current_password': 'test-pass-123',
            'email-new_email': 'after@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Посилання надіслано', response.json()['html'])
        self.assertEqual(len(mail.outbox), 1)
        link = re.search(r'http://testserver(\S+)', mail.outbox[0].body).group(1)
        self.assertContains(self.client.get(link), 'after@example.com')
        self.assertRedirects(self.client.post(link), reverse('profile_page'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'after@example.com')

    def test_rate_limit_shows_feedback(self):
        cache.set(f'profile-mail:{self.user.pk}:password', True, 60)
        response = self.client.post(reverse('profile'), {'action': 'password'})
        self.assertEqual(response.status_code, 429)
        self.assertIn('Зачекайте хвилину', response.json()['html'])

    def test_invalid_email_form_remains_expanded(self):
        response = self.client.post(reverse('profile'), {
            'action': 'email', 'email-current_password': 'wrong',
            'email-new_email': 'after@example.com',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('class="profile-action-card" open', response.json()['html'])
        self.assertIn('Неправильний поточний пароль', response.json()['html'])
