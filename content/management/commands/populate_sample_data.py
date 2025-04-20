import os
import hashlib
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from content.models import Marker, MarkerFile
from django.utils.text import slugify

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample marker data and users'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting sample data population'))
        
        # Create sample users
        self.create_users()
        
        # Create sample markers
        self.create_markers()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated sample data'))

    def create_users(self):
        self.stdout.write(self.style.SUCCESS('Creating sample users'))
        
        users = [
            {
                "username": "oleksandr_v",
                "email": "oleksandr_v@example.com",
                "password": "securepass123"
            },
            {
                "username": "intel_analyst",
                "email": "intel_analyst@example.com",
                "password": "intel2024"
            },
            {
                "username": "safety_coordinator",
                "email": "safety_coordinator@example.com",
                "password": "safety2024"
            },
            {
                "username": "emergency_response",
                "email": "emergency_response@example.com",
                "password": "emergency2024"
            },
            {
                "username": "ai_detection_system",
                "email": "ai_system@example.com",
                "password": "aidetect2024"
            },
            {
                "username": "utilities_inspector",
                "email": "utilities_inspector@example.com",
                "password": "utilities2024"
            },
            {
                "username": "education_worker",
                "email": "education_worker@example.com",
                "password": "education2024"
            },
            {
                "username": "intel_researcher",
                "email": "intel_researcher@example.com",
                "password": "research2024"
            },
            {
                "username": "environmental_watch",
                "email": "environmental_watch@example.com",
                "password": "environment2024"
            },
            {
                "username": "humanitarian_aid",
                "email": "humanitarian_aid@example.com",
                "password": "humanitarian2024"
            },
            {
                "username": "infrastructure_watch",
                "email": "infrastructure_watch@example.com",
                "password": "infrastructure2024"
            },
            {
                "username": "aviation_tracker",
                "email": "aviation_tracker@example.com",
                "password": "aviation2024"
            }
        ]
        
        created_count = 0
        for user_data in users:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                    "is_active": True,
                    "date_joined": datetime.datetime.now()
                }
            )
            
            if created:
                user.set_password(user_data["password"])
                user.save()
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created user: {user.username}"))
            else:
                self.stdout.write(self.style.WARNING(f"User already exists: {user.username}"))
        
        self.stdout.write(self.style.SUCCESS(f"Created {created_count} users"))

    def create_markers(self):
        self.stdout.write(self.style.SUCCESS('Creating sample markers'))
        
        marker_data = [
            {
                "title": "Пошкоджений міст у Харківській області",
                "description": "Міст через річку Сіверський Донець зазнав значних пошкоджень. Перехід неможливий для транспортних засобів, але пішоходи можуть використовувати тимчасові настили.",
                "latitude": 49.9456,
                "longitude": 36.2988,
                "category": "infrastructure",
                "verification": "verified",
                "confidence": 92,
                "date": "2024-03-15",
                "source": "Місцевий волонтер",
                "user": "oleksandr_v"
            },
            {
                "title": "Військовий блокпост біля Ізюма",
                "description": "Укріплений блокпост з бронетехнікою та протитанковими загородженнями. Контролює головний в'їзд до міста зі східного напрямку.",
                "latitude": 49.1916,
                "longitude": 37.2567,
                "category": "military",
                "verification": "verified",
                "confidence": 88,
                "date": "2024-03-20",
                "source": "Супутникові знімки",
                "user": "intel_analyst"
            },
            {
                "title": "Замінована ділянка поля",
                "description": "Сільськогосподарське поле біля села Вовчанськ, що ймовірно містить протипіхотні та протитанкові міни. Територія позначена попереджувальними знаками.",
                "latitude": 50.2953,
                "longitude": 36.9522,
                "category": "hazard",
                "verification": "unverified",
                "confidence": 75,
                "date": "2024-02-28",
                "source": "Повідомлення місцевих жителів",
                "user": "safety_coordinator"
            },
            {
                "title": "Пошкоджений житловий комплекс у Миколаєві",
                "description": "П'ятиповерховий житловий будинок з частково зруйнованим дахом та пошкодженнями верхніх поверхів. Евакуація мешканців проведена, територія огороджена.",
                "latitude": 46.9700,
                "longitude": 31.9798,
                "category": "residential",
                "verification": "verified",
                "confidence": 95,
                "date": "2024-03-05",
                "source": "Державна служба з надзвичайних ситуацій",
                "user": "emergency_response"
            },
            {
                "title": "Склад боєприпасів біля Бахмута",
                "description": "Підозрювана локація складу боєприпасів у лісовій зоні. Спостерігається підвищена активність вантажного транспорту в нічний час.",
                "latitude": 48.5881,
                "longitude": 38.0002,
                "category": "military",
                "verification": "ai-detected",
                "confidence": 67,
                "date": "2024-03-18",
                "source": "Аналіз нічних теплових знімків",
                "user": "ai_detection_system"
            },
            {
                "title": "Пошкоджена електропідстанція у Сумській області",
                "description": "Районна електропідстанція зазнала пошкоджень внаслідок обстрілу. Тимчасово відключене електропостачання у трьох сусідніх селах.",
                "latitude": 51.3322,
                "longitude": 33.9680,
                "category": "infrastructure",
                "verification": "verified",
                "confidence": 91,
                "date": "2024-03-12",
                "source": "Звіт енергетичної компанії",
                "user": "utilities_inspector"
            },
            {
                "title": "Зруйнована школа в Краматорську",
                "description": "Будівля загальноосвітньої школи №5 зазнала значних пошкоджень. Заняття перенесені до сусідніх навчальних закладів.",
                "latitude": 48.7215,
                "longitude": 37.5654,
                "category": "infrastructure",
                "verification": "unverified",
                "confidence": 82,
                "date": "2024-03-02",
                "source": "Місцеві ЗМІ",
                "user": "education_worker"
            },
            {
                "title": "Протиповітряні укріплення на околицях Дніпра",
                "description": "Система протиповітряної оборони на південно-східній околиці міста. Включає радари та зенітно-ракетні комплекси.",
                "latitude": 48.4198,
                "longitude": 35.0724,
                "category": "military",
                "verification": "disputed",
                "confidence": 58,
                "date": "2024-03-25",
                "source": "Анонімний звіт",
                "user": "intel_researcher"
            },
            {
                "title": "Забруднення річки в Черкаській області",
                "description": "Можливе хімічне забруднення річки внаслідок пошкодження промислового об'єкту. Спостерігається підвищена загибель риби та зміна кольору води.",
                "latitude": 49.4285,
                "longitude": 32.0645,
                "category": "hazard",
                "verification": "pending",
                "confidence": 63,
                "date": "2024-03-22",
                "source": "Екологічний моніторинг",
                "user": "environmental_watch"
            },
            {
                "title": "Евакуаційний пункт у Запоріжжі",
                "description": "Організований пункт евакуації та допомоги біженцям у спортивному комплексі. Надаються харчування, медична допомога та тимчасовий притулок.",
                "latitude": 47.8567,
                "longitude": 35.1232,
                "category": "residential",
                "verification": "verified",
                "confidence": 98,
                "date": "2024-03-01",
                "source": "Гуманітарна організація",
                "user": "humanitarian_aid"
            },
            {
                "title": "Пошкоджений газопровід у Чернігівській області",
                "description": "Магістральний газопровід зазнав пошкоджень внаслідок вибуху. Ремонтні бригади працюють над відновленням постачання газу.",
                "latitude": 51.5055,
                "longitude": 31.2820,
                "category": "infrastructure",
                "verification": "ai-detected",
                "confidence": 72,
                "date": "2024-03-17",
                "source": "Супутниковий моніторинг",
                "user": "infrastructure_watch"
            },
            {
                "title": "Військовий аеродром біля Житомира",
                "description": "Активний військовий аеродром з ознаками підвищеної авіаційної активності. Спостерігається приліт та відліт транспортних літаків.",
                "latitude": 50.2515,
                "longitude": 28.7358,
                "category": "military",
                "verification": "verified",
                "confidence": 89,
                "date": "2024-03-21",
                "source": "Аналіз відкритих даних польотів",
                "user": "aviation_tracker"
            }
        ]
        
        created_count = 0
        for data in marker_data:
            # Get the user
            username = data.pop("user")
            try:
                user = User.objects.get(username=username)
                
                # Parse date
                date_str = data.pop("date")
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                
                # Create marker
                marker, created = Marker.objects.get_or_create(
                    title=data["title"],
                    latitude=data["latitude"],
                    longitude=data["longitude"],
                    defaults={
                        "description": data["description"],
                        "category": data["category"],
                        "verification": data["verification"],
                        "confidence": data["confidence"],
                        "source": data["source"],
                        "date": date_obj,
                        "user": user
                    }
                )
                
                if created:
                    created_count += 1
                    # Create a placeholder for the image file
                    placeholder_name = f"marker_{marker.id}_placeholder"
                    placeholder_path = os.path.join('placeholders', f"{slugify(placeholder_name)}.txt")
                    
                    # Create a marker file entry (you'll upload actual images later)
                    MarkerFile.objects.create(
                        marker=marker,
                        file=placeholder_path,
                        uploaded_at=datetime.datetime.now()
                    )
                    
                    self.stdout.write(self.style.SUCCESS(f"Created marker: {marker.title}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Marker already exists: {data['title']}"))
                    
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User not found: {username}"))
        
        self.stdout.write(self.style.SUCCESS(f"Created {created_count} markers"))
        