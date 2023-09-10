from django.test import TestCase
from django.contrib.auth.models import User
from .models import Competition, Judge, PrelimsRegistration

class CompetitionRegistrationTest(TestCase):
    def setUp(self):
        # Create 6 judges

        passwords = [
            r'$@#$Vd3@$',
            r'Ab3f%O?06',
            r'#@lv8l#p1',
            r'o&9A@54&V',
            r'XKrKD$&0j',
            r'@41G939K6',
        ]

        self.judges = []
        for i in range(1, 7):
            judge = User.objects.create_user(
                username=f'judge{i}',
                password=passwords[i],
            )
            self.judges.append(judge)
            Judge.objects.create(user=judge)

    def test_competition_registration(self):
        # Log in as admin (you can use Client.login)
        self.client.login(username='toweeelie', password='SurStroMMing@666')

        # Create a new competition
        competition_data = {
            'title': 'Test Competition',
            'comp_roles':('Leader','Follower'),
        }

        response = self.client.post('/admin/testapp/competition/add/', competition_data)
        self.assertEqual(response.status_code, 302)  # Check for successful creation (HTTP 302)

        self.client.logout()
'''
        # Register 24 competitors
        for i in range(1, 25):
            response = self.client.post('/register_competitor/', {'name': f'Competitor {i}'})
            self.assertEqual(response.status_code, 302)  # Check for successful registration (HTTP 302)

        # Verify that there are now 24 registered competitors for the competition
        competition = Competition.objects.get(title='Test Competition')
        registered_competitors = PrelimsRegistration.objects.filter(competition=competition)
        self.assertEqual(registered_competitors.count(), 24)
'''