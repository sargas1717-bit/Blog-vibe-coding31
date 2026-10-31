from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Post


User = get_user_model()


class PostAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='StrongPass123!')
        self.other_user = User.objects.create_user(username='other', password='StrongPass123!')
        self.post = Post.objects.create(
            title='Private ownership test',
            content='Original content',
            author=self.owner,
        )

    def test_list_and_detail_are_public(self):
        self.assertEqual(self.client.get(reverse('post_list')).status_code, 200)
        self.assertEqual(
            self.client.get(reverse('post_detail', kwargs={'pk': self.post.pk})).status_code,
            200,
        )

    def test_anonymous_users_are_redirected_from_mutation_views(self):
        create_response = self.client.get(reverse('post_create'))
        update_response = self.client.get(reverse('post_update', kwargs={'pk': self.post.pk}))
        delete_response = self.client.get(reverse('post_delete', kwargs={'pk': self.post.pk}))

        self.assertRedirects(create_response, f"{reverse('login')}?next={reverse('post_create')}")
        self.assertEqual(update_response.status_code, 302)
        self.assertEqual(delete_response.status_code, 302)

    def test_create_uses_authenticated_user_and_rejects_author_field(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse('post_create'),
            {
                'title': 'Created safely',
                'content': 'Created content',
                'author': self.owner.pk,
            },
        )

        created_post = Post.objects.get(title='Created safely')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(created_post.author, self.other_user)
        self.assertNotContains(self.client.get(reverse('post_create')), 'name="author"')

    def test_owner_can_update_and_delete_post(self):
        self.client.force_login(self.owner)

        update_response = self.client.post(
            reverse('post_update', kwargs={'pk': self.post.pk}),
            {'title': 'Updated by owner', 'content': 'Updated content'},
        )
        self.assertEqual(update_response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated by owner')

        delete_response = self.client.post(reverse('post_delete', kwargs={'pk': self.post.pk}))
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_other_user_cannot_update_or_delete_post(self):
        self.client.force_login(self.other_user)

        update_response = self.client.post(
            reverse('post_update', kwargs={'pk': self.post.pk}),
            {'title': 'Hijacked title', 'content': 'Hijacked content'},
        )
        delete_response = self.client.post(reverse('post_delete', kwargs={'pk': self.post.pk}))

        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Private ownership test')
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_delete_is_not_allowed_with_get(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('post_delete', kwargs={'pk': self.post.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_csrf_is_required_for_delete_post(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.owner)
        delete_url = reverse('post_delete', kwargs={'pk': self.post.pk})

        csrf_client.get(delete_url)
        response = csrf_client.post(delete_url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_detail_shows_controls_only_to_author(self):
        owner_client = Client()
        owner_client.force_login(self.owner)
        other_client = Client()
        other_client.force_login(self.other_user)
        detail_url = reverse('post_detail', kwargs={'pk': self.post.pk})

        self.assertContains(owner_client.get(detail_url), reverse('post_update', kwargs={'pk': self.post.pk}))
        self.assertNotContains(other_client.get(detail_url), reverse('post_update', kwargs={'pk': self.post.pk}))


class SignUpTests(TestCase):
    def test_signup_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'new-reader',
                'password1': 'ValidPassword123!',
                'password2': 'ValidPassword123!',
            },
        )

        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='new-reader').exists())