from django.test import TestCase
from django.contrib.auth.models import User
from .models import Competition, Judge, Registration


crown_bar_jnj ={
    'judges':{
        'j1':'Марія Тітова',
        'j2':'Світлана Матових',
        'j3':'Саша Мосійчук',
        'j4':'СергійБ Безуглий',
        'j5':'Максим Болгов',
        'j6':'Сергій Ковальов',
    },
    'passwords':{
        'j1':r'$@#$Vd3@$',
        'j2':r'Ab3f%O?06',
        'j3':r'#@lv8l#p1',
        'j4':r'o&9A@54&V',
        'j5':r'XKrKD$&0j',
        'j6':r'@41G939K6',
    },
    'leaders':{
        1:'Влад Володько',
        3:'Антон Мордерер',
        5:'Влад Денисенко',
        7:'Денис Герасименко',
        9:'Ярослав Щербак',
        11:'Богдан Левченко',
        13:'Антон Дрейман',
        15:'Андрій Кислюк',
        17:'Олексій Мірошниченко',
        19:'Костянтин Гірлянд',
        21:'Костя Орленко',
        #23:'Максим РДС',
    },
    'followers':{
        2:'Катя Бенке',
        4:'Єва Місілюк',
        6:'Ксюша Венедиктова',
        8:'Яна Завгородня',
        10:'Ольга Коваленко',
        12:'Настя Мурга',
        14:'Олена Дорош',
        16:'Катя Безверха',
        18:'Наталя Гірлянд',
        20:'Даша Трофіменко',
        22:'Вова Лозовий',
        #24:'Ліза РДС',
    },
    'prelims':{
        'points':{
            'j1':{1:'Mb',3:'Y',7:'Y',17:'Y',19:'Mb',21:'Y'},
            'j2':{3:'Y',7:'Y',17:'Y',21:'Y',5:'Mb',19:'Mb'},
            'j3':{3:'Y',7:'Y',17:'Y',21:'Mb',1:'Y',5:'Mb'},
            'j4':{2:'Y',14:'Y',8:'Y',20:'Y',12:'Mb',16:'Mb'},
            'j5':{2:'Y',14:'Y',22:'Y',20:'Mb',12:'Mb',18:'Y'},
            'j6':{2:'Y',14:'Mb',8:'Y',22:'Y',20:'Mb',12:'Y'},
        },
        'finalists':{
            'leaders':(1,3,7,17,21),
            'followers':(2,8,14,20,22),
        },
    },
    'finals':{
        'pairs':{
            'p1':(21,20),
            'p2':(7,14),
            'p3':(3,8),
            'p4':(1,2),
            'p5':(17,22),
        },
        'points':{
            'j1':{'p1':2,'p2':1,'p3':4,'p4':5,'p5':3},
            'j2':{'p1':2,'p2':3,'p3':4,'p4':5,'p5':1},
            'j3':{'p1':4,'p2':5,'p3':2,'p4':3,'p5':1},
            'j4':{'p1':4,'p2':5,'p3':1,'p4':2,'p5':3},
            'j5':{'p1':4,'p2':2,'p3':3,'p4':5,'p5':1},
        },
        'places':{1:'p5',2:'p3',3:'p2',4:'p1',5:'p4'},
    },
}


class CompetitionRegistrationTest(TestCase):
    def setUp(self):
        # Create judges 
        self.judges = []
        for j,p in crown_bar_jnj['passwords'].items():
            judge = User.objects.create_user(
                username=j,
                password=p,
                first_name=crown_bar_jnj['judges'][j].split()[0],
                last_name=crown_bar_jnj['judges'][j].split()[1],
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