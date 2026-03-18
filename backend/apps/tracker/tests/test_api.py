"""
UniTrack — Backend Test Suite
Tests all API endpoints, auth, permissions, and edge cases.
Run with: python manage.py test apps.tracker.tests apps.users
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User
from apps.tracker.models import Principle, Task


def make_user(email='test@test.com', password='pass1234'):
    return User.objects.create_user(email=email, password=password, full_name='Test User')


def make_principle(user, name='Math', semester='Semester 1', color='#c8f55a'):
    return Principle.objects.create(user=user, name=name, semester=semester, color=color)


def make_task(principle, text='Study chapter 1', priority='medium'):
    return Task.objects.create(principle=principle, text=text, priority=priority)


# ── AUTH TESTS ──────────────────────────────────────────────────────────────

class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    def test_register_success(self):
        res = self.client.post('/api/auth/register/', {
            'email': 'new@test.com',
            'password': 'newpass123',
            'password2': 'newpass123',
            'full_name': 'New User',
        })
        self.assertEqual(res.status_code, 201)
        self.assertTrue(User.objects.filter(email='new@test.com').exists())

    def test_register_password_mismatch(self):
        res = self.client.post('/api/auth/register/', {
            'email': 'x@test.com',
            'password': 'pass1234',
            'password2': 'different',
            'full_name': 'X',
        })
        self.assertEqual(res.status_code, 400)

    def test_register_duplicate_email(self):
        res = self.client.post('/api/auth/register/', {
            'email': 'test@test.com',
            'password': 'pass1234',
            'password2': 'pass1234',
            'full_name': 'Dup',
        })
        self.assertEqual(res.status_code, 400)

    def test_login_success(self):
        res = self.client.post('/api/auth/login/', {
            'email': 'test@test.com',
            'password': 'pass1234',
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertIn('user', res.data)
        self.assertEqual(res.data['user']['email'], 'test@test.com')

    def test_login_wrong_password(self):
        res = self.client.post('/api/auth/login/', {
            'email': 'test@test.com',
            'password': 'wrongpass',
        })
        self.assertEqual(res.status_code, 401)

    def test_protected_endpoint_without_token(self):
        res = self.client.get('/api/principles/')
        self.assertEqual(res.status_code, 401)

    def test_profile_get(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/auth/profile/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['email'], self.user.email)

    def test_profile_cannot_change_email(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.patch('/api/auth/profile/', {'email': 'hacked@evil.com'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'test@test.com')  # email unchanged

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/auth/change-password/', {
            'old_password': 'pass1234',
            'new_password': 'newpass456',
            'new_password2': 'newpass456',
        })
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456'))

    def test_change_password_wrong_old(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/auth/change-password/', {
            'old_password': 'wrongpass',
            'new_password': 'newpass456',
            'new_password2': 'newpass456',
        })
        self.assertEqual(res.status_code, 400)


# ── PRINCIPLE TESTS ─────────────────────────────────────────────────────────

class PrincipleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.other_user = make_user(email='other@test.com')
        self.client.force_authenticate(user=self.user)

    def test_create_principle(self):
        res = self.client.post('/api/principles/', {
            'name': 'Calculus',
            'semester': 'Semester 1',
            'color': '#c8f55a',
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['name'], 'Calculus')
        self.assertEqual(Principle.objects.filter(user=self.user).count(), 1)

    def test_create_principle_blank_name(self):
        res = self.client.post('/api/principles/', {'name': '   '})
        self.assertEqual(res.status_code, 400)

    def test_list_only_own_principles(self):
        make_principle(self.user, 'Mine')
        make_principle(self.other_user, 'Theirs')
        res = self.client.get('/api/principles/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['name'], 'Mine')

    def test_get_principle_detail(self):
        p = make_principle(self.user, 'Physics')
        res = self.client.get(f'/api/principles/{p.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['name'], 'Physics')

    def test_cannot_access_other_users_principle(self):
        p = make_principle(self.other_user, 'Secret')
        res = self.client.get(f'/api/principles/{p.id}/')
        self.assertEqual(res.status_code, 404)

    def test_update_principle(self):
        p = make_principle(self.user, 'Old Name')
        res = self.client.patch(f'/api/principles/{p.id}/', {'name': 'New Name'})
        self.assertEqual(res.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.name, 'New Name')

    def test_delete_principle(self):
        p = make_principle(self.user)
        res = self.client.delete(f'/api/principles/{p.id}/')
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Principle.objects.filter(id=p.id).exists())

    def test_cannot_delete_other_users_principle(self):
        p = make_principle(self.other_user)
        res = self.client.delete(f'/api/principles/{p.id}/')
        self.assertEqual(res.status_code, 404)
        self.assertTrue(Principle.objects.filter(id=p.id).exists())

    def test_archive_toggle(self):
        p = make_principle(self.user)
        self.assertFalse(p.is_archived)
        # Archive
        res = self.client.post(f'/api/principles/{p.id}/archive/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['is_archived'])
        p.refresh_from_db()
        self.assertTrue(p.is_archived)
        # Unarchive
        res = self.client.post(f'/api/principles/{p.id}/archive/')
        self.assertFalse(res.data['is_archived'])

    def test_archive_does_not_crash(self):
        """Regression: save(update_fields=['is_archived','updated_at']) crashed with auto_now fields"""
        p = make_principle(self.user)
        try:
            res = self.client.post(f'/api/principles/{p.id}/archive/')
            self.assertEqual(res.status_code, 200)
        except Exception as e:
            self.fail(f'archive() raised an exception: {e}')

    def test_search_principles(self):
        make_principle(self.user, 'Calculus')
        make_principle(self.user, 'Physics')
        res = self.client.get('/api/principles/?search=calc')
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['name'], 'Calculus')

    def test_filter_archived(self):
        p1 = make_principle(self.user, 'Active')
        p2 = make_principle(self.user, 'Archived')
        p2.is_archived = True
        p2.save()
        res = self.client.get('/api/principles/?is_archived=false')
        names = [r['name'] for r in res.data['results']]
        self.assertIn('Active', names)
        self.assertNotIn('Archived', names)

    def test_stats_empty(self):
        res = self.client.get('/api/principles/stats/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['total_principles'], 0)
        self.assertEqual(res.data['overall_progress'], 0)

    def test_stats_with_data(self):
        p = make_principle(self.user)
        t1 = make_task(p, 'Task 1')
        t2 = make_task(p, 'Task 2')
        t1.is_done = True
        t1.save()
        res = self.client.get('/api/principles/stats/')
        self.assertEqual(res.data['total_tasks'], 2)
        self.assertEqual(res.data['completed_tasks'], 1)
        self.assertEqual(res.data['overall_progress'], 50.0)

    def test_progress_percentage(self):
        p = make_principle(self.user)
        self.assertEqual(p.progress_percentage, 0)  # no tasks
        t1 = make_task(p)
        t1.is_done = True
        t1.save()
        t2 = make_task(p, 'Task 2')
        p.refresh_from_db()
        self.assertEqual(p.progress_percentage, 50)


# ── TASK TESTS ───────────────────────────────────────────────────────────────

class TaskTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.other_user = make_user(email='other@test.com')
        self.principle = make_principle(self.user)
        self.client.force_authenticate(user=self.user)

    def test_create_task(self):
        res = self.client.post('/api/tasks/', {
            'principle': self.principle.id,
            'text': 'Read chapter 1',
            'priority': 'high',
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['text'], 'Read chapter 1')
        self.assertFalse(res.data['is_done'])

    def test_create_task_blank_text(self):
        res = self.client.post('/api/tasks/', {
            'principle': self.principle.id,
            'text': '   ',
        })
        self.assertEqual(res.status_code, 400)

    def test_cannot_create_task_on_other_users_principle(self):
        other_principle = make_principle(self.other_user, 'Other')
        res = self.client.post('/api/tasks/', {
            'principle': other_principle.id,
            'text': 'Sneaky task',
        })
        self.assertIn(res.status_code, [400, 403])

    def test_toggle_task(self):
        task = make_task(self.principle)
        self.assertFalse(task.is_done)
        res = self.client.post(f'/api/tasks/{task.id}/toggle/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['is_done'])
        self.assertIsNotNone(res.data['done_at'])
        # Toggle back
        res = self.client.post(f'/api/tasks/{task.id}/toggle/')
        self.assertFalse(res.data['is_done'])
        self.assertIsNone(res.data['done_at'])

    def test_update_task_text(self):
        task = make_task(self.principle, 'Old text')
        res = self.client.patch(f'/api/tasks/{task.id}/', {'text': 'New text'})
        self.assertEqual(res.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.text, 'New text')

    def test_update_task_priority(self):
        task = make_task(self.principle, priority='low')
        res = self.client.patch(f'/api/tasks/{task.id}/', {'priority': 'high'})
        self.assertEqual(res.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.priority, 'high')

    def test_update_task_due_date(self):
        task = make_task(self.principle)
        res = self.client.patch(f'/api/tasks/{task.id}/', {'due_date': '2026-06-01'})
        self.assertEqual(res.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(str(task.due_date), '2026-06-01')

    def test_delete_task(self):
        task = make_task(self.principle)
        res = self.client.delete(f'/api/tasks/{task.id}/')
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_cannot_access_other_users_task(self):
        other_principle = make_principle(self.other_user)
        other_task = make_task(other_principle, 'Secret')
        res = self.client.get(f'/api/tasks/{other_task.id}/')
        self.assertEqual(res.status_code, 404)

    def test_tasks_deleted_with_principle(self):
        task = make_task(self.principle)
        task_id = task.id
        self.principle.delete()
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_done_at_set_on_toggle(self):
        task = make_task(self.principle)
        self.assertIsNone(task.done_at)
        task.is_done = True
        task.save()
        task.refresh_from_db()
        self.assertIsNotNone(task.done_at)

    def test_done_at_cleared_on_untoggle(self):
        task = make_task(self.principle)
        task.is_done = True
        task.save()
        task.is_done = False
        task.save()
        task.refresh_from_db()
        self.assertIsNone(task.done_at)

    def test_filter_tasks_by_done(self):
        t1 = make_task(self.principle, 'Done task')
        t1.is_done = True
        t1.save()
        make_task(self.principle, 'Pending task')
        res = self.client.get(f'/api/tasks/?principle={self.principle.id}&is_done=true')
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['text'], 'Done task')
