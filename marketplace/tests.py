from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_index_loads(self):
        response = self.client.get(reverse("marketplace:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "StudiServ")
        self.assertContains(response, "Marketplace de services")
        self.assertNotContains(response, "Cahier des charges")

    def test_role_login_pages_load(self):
        student_response = self.client.get(reverse("marketplace:login_etudiant"))
        provider_response = self.client.get(reverse("marketplace:login_prestataire"))

        self.assertEqual(student_response.status_code, 200)
        self.assertEqual(provider_response.status_code, 200)
        self.assertContains(student_response, "Connexion etudiant")
        self.assertContains(provider_response, "Connexion prestataire")

    def test_main_login_and_dashboard_routes(self):
        login_response = self.client.get(reverse("marketplace:login"))
        student_redirect = self.client.get(reverse("marketplace:etudiant_dashboard"))
        provider_redirect = self.client.get(reverse("marketplace:prestatire_dashboard"))

        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, "/login")
        self.assertEqual(student_redirect.status_code, 302)
        self.assertEqual(provider_redirect.status_code, 302)

    def test_login_redirects_to_student_dashboard(self):
        User.objects.create_user(username="eya", password="testpass123")

        response = self.client.post(
            reverse("marketplace:login"),
            {"username": "eya", "password": "testpass123"},
        )

        self.assertRedirects(response, reverse("marketplace:etudiant_dashboard"))
