from random import choice as rc
from random import sample
from faker import Faker
from app import app
from models import db, User, MoreDetail, Service
from werkzeug.security import generate_password_hash

fake = Faker()

with app.app_context():
    print("Deleting all records...")
    MoreDetail.query.delete()
    Service.query.delete()
    User.query.delete()

    print("Creating items...")

    job_titles = [
        "Plumber", "Electrician", "Painter", "Mechanic", "Cleaner",
        "Welder", "Gardener", "Technician", "Carpenter", "AC Repair Specialist"
    ]

    categories = ["Home Services", "Auto Services", "Electrical", "Maintenance", "Outdoor"]
    locations = ["Nairobi", "Mombasa", "Kisumu", "Eldoret", "Thika", "Machakos", "Naivasha"]

    services_list = [
        "Fix Sink", "Install Lights", "Paint Room", "Car Service", "General Cleaning",
        "Welding", "Trim Hedges", "Repair AC", "Build Cabinets", "Fix Wiring",
        "Garden Maintenance", "Install CCTV", "Window Repair", "Tile Installation", "Ceiling Repair"
    ]

    for _ in range(20):
        first_name = fake.first_name()
        last_name = fake.last_name()
        username = fake.user_name()
        email = fake.email()
        password = generate_password_hash("password123")

        user = User(
            first_name=first_name,
            last_name=last_name,
            display_name=f"{first_name} {last_name}",
            date_of_birth=fake.date_of_birth(minimum_age=20, maximum_age=50),
            email=email,
            username=username,
            password=password,
            role="Worker"
        )

        db.session.add(user)
        db.session.flush()  # Make sure user.id is available

        more_detail = MoreDetail(
            category=rc(categories),
            jobTitle=rc(job_titles),
            description=fake.sentence(),
            detailedDescription = fake.paragraph(nb_sentences=20),
            payRate=f"${fake.random_int(min=500, max=2000)}",
            completionRate=f"{fake.random_int(min=80, max=100)}%",
            rating=str(round(fake.pyfloat(min_value=3.0, max_value=5.0), 1)),
            location=rc(locations),
            responseTime=f"{fake.random_int(min=1, max=24)} hrs",
            user_id=user.id
        )

        db.session.add(more_detail)

        # ✅ Assign at least 3 unique services to each user
        selected_services = sample(services_list, 5)
        for service_name in selected_services:
            service = Service(service=service_name, user_id=user.id)
            db.session.add(service)

    db.session.commit()
    print("Items created successfully!")
