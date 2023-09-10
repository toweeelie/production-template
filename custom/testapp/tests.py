from django.test import TestCase
from django.contrib.auth.models import User
from .models import Competition, Judge, PrelimsRegistration

class CompetitionRegistrationTest(TestCase):
    def setUp(self):
        # Create 6 judges
        self.judges = []
        for i in range(1, 7):
            judge = User.objects.create_user(
                username=f'judge{i}',
                password=f'password{i}',
            )
            self.judges.append(judge)
            Judge.objects.create(user=judge)

    def test_competition_registration(self):
        # Log in as one of the judges (you can use Client.login)
        judge_user = self.judges[0]
        self.client.login(username=judge_user.username, password=f'password1')

        # Create a new competition
        response = self.client.post('/create_competition/', {'name': 'Test Competition'})
        self.assertEqual(response.status_code, 302)  # Check for successful creation (HTTP 302)

        # Register 24 competitors
        for i in range(1, 25):
            response = self.client.post('/register_competitor/', {'name': f'Competitor {i}'})
            self.assertEqual(response.status_code, 302)  # Check for successful registration (HTTP 302)

        # Verify that there are now 24 registered competitors for the competition
        competition = Competition.objects.get(name='Test Competition')
        registered_competitors = PrelimsRegistration.objects.filter(competition=competition)
        self.assertEqual(registered_competitors.count(), 24)
