#chatbot_service\tests\utils
import os
import sys
from datetime import datetime, timedelta, date
import random
from passlib.context import CryptContext
import faker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_manager import Base, engine, SessionLocal
from models.user import User
from models.health_streak import HealthActivity, UserStreak, StreakCompletion
from models.badge import Badge, UserBadge
from models.blog import Category, Tag, Article, article_tags

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
fake = faker.Faker()

def create_tables():
    """Create all tables defined in the models"""
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables created successfully")

def drop_tables():
    """Drop all tables defined in the models"""
    Base.metadata.drop_all(bind=engine)
    print("❌ All database tables dropped")

def create_mock_users(session, count=10):
    """Create mock users"""
    users = []
    for i in range(count):
        is_admin = i == 0  # First user is admin
        hashed_password = pwd_context.hash("password123" if not is_admin else "admin123")
        
        user = User(
            username=fake.user_name() if i > 0 else "admin",
            email=fake.email() if i > 0 else "admin@carebot.com",
            password_hash=hashed_password,
            created_at=fake.date_time_between(start_date='-1y', end_date='now'),
        )
        users.append(user)
    
    session.add_all(users)
    session.commit()
    print(f"✅ Created {count} mock users")
    return users

def create_health_activities(session):
    """Create health activities"""
    activities = [
        HealthActivity(name="Daily Walk", description="Take a 30-minute walk", difficulty="easy"),
        HealthActivity(name="Meditation", description="10 minutes of mindfulness meditation", difficulty="easy"),
        HealthActivity(name="Drink Water", description="Drink 8 glasses of water", difficulty="easy"),
        HealthActivity(name="Strength Training", description="30 minutes of strength exercises", difficulty="medium"),
        HealthActivity(name="Yoga Session", description="45 minutes of yoga practice", difficulty="medium"),
        HealthActivity(name="Cardio Workout", description="30 minutes of high-intensity cardio", difficulty="hard"),
        HealthActivity(name="8 Hours Sleep", description="Get 8 hours of quality sleep", difficulty="medium"),
        HealthActivity(name="Healthy Meal", description="Prepare a balanced, nutritious meal", difficulty="medium"),
        HealthActivity(name="No Processed Sugar", description="Avoid processed sugar for the whole day", difficulty="hard"),
        HealthActivity(name="Screen Time Limit", description="Limit recreational screen time to 2 hours", difficulty="medium"),
    ]
    
    session.add_all(activities)
    session.commit()
    print(f"✅ Created {len(activities)} health activities")
    return activities

def create_user_streaks(session, users, activities):
    """Create user streaks for activities"""
    user_streaks = []
    
    for user in users:
        # Each user follows 3-7 random activities
        user_activities = random.sample(activities, random.randint(3, min(7, len(activities))))
        
        for activity in user_activities:
            # Generate random streak data
            current_streak = random.randint(0, 15)
            longest_streak = random.randint(current_streak, current_streak + 20)
            
            last_completed = None
            if current_streak > 0:
                last_completed = datetime.now() - timedelta(days=random.randint(0, 2))
            
            user_streak = UserStreak(
                user_id=user.id,
                activity_id=activity.id,
                current_streak=current_streak,
                longest_streak=longest_streak,
                last_completed=last_completed
            )
            user_streaks.append(user_streak)
    
    session.add_all(user_streaks)
    session.commit()
    print(f"✅ Created {len(user_streaks)} user streaks")
    return user_streaks

def create_streak_completions(session, user_streaks):
    """Create streak completion history"""
    completions = []
    
    for user_streak in user_streaks:
        # Create completion history for the past 30 days
        # with random completions matching the current streak
        today = date.today()
        
        # Create some history data
        for day_offset in range(30, 0, -1):
            completion_date = today - timedelta(days=day_offset)
            
            # Decide if this date has a completion
            # More likely to have recent completions to match current streak
            has_completion = False
            
            # For users with current streaks, ensure the recent days have completions
            if user_streak.current_streak > 0 and day_offset <= user_streak.current_streak:
                has_completion = True
            elif random.random() < 0.4:  # 40% chance of historical completion
                has_completion = True
                
            if has_completion:
                completion = StreakCompletion(
                    user_id=user_streak.user_id,
                    activity_id=user_streak.activity_id,
                    completed_date=completion_date
                )
                completions.append(completion)
    
    session.add_all(completions)
    session.commit()
    print(f"✅ Created {len(completions)} streak completions")

def create_badges(session):
    """Create achievement badges"""
    badges = [
        Badge(name="Early Bird", description="Complete a health activity before 8 AM", image_url="/badges/early_bird.png"),
        Badge(name="Consistency Master", description="Maintain any streak for 7 days", image_url="/badges/consistency.png"),
        Badge(name="Health Champion", description="Reach a 30-day streak", image_url="/badges/champion.png"),
        Badge(name="Overachiever", description="Complete 3 different activities in one day", image_url="/badges/overachiever.png"),
        Badge(name="Wellness Warrior", description="Complete 10 hard difficulty activities", image_url="/badges/warrior.png"),
        Badge(name="Mindfulness Guru", description="Complete meditation 15 times", image_url="/badges/mindfulness.png"),
        Badge(name="Hydration Hero", description="Complete the water drinking goal 20 times", image_url="/badges/hydration.png"),
        Badge(name="Sleep Master", description="Achieve 8 hours of sleep 10 nights in a row", image_url="/badges/sleep.png"),
    ]
    
    session.add_all(badges)
    session.commit()
    print(f"✅ Created {len(badges)} badges")
    return badges

def assign_user_badges(session, users, badges):
    """Assign random badges to users"""
    user_badges = []
    
    for user in users:
        # Each user gets 0-5 random badges
        user_badge_count = random.randint(0, min(5, len(badges)))
        if user_badge_count > 0:
            user_badges_list = random.sample(badges, user_badge_count)
            
            for badge in user_badges_list:
                # Random earned date in the past 3 months
                earned_at = fake.date_time_between(start_date='-3M', end_date='now')
                
                user_badge = UserBadge(
                    user_id=user.id,
                    badge_id=badge.id,
                    earned_at=earned_at
                )
                user_badges.append(user_badge)
    
    session.add_all(user_badges)
    session.commit()
    print(f"✅ Created {len(user_badges)} user badges")

def create_blog_content(session, users):
    """Create categories, tags, and articles for the blog section"""
    # Create categories
    categories = [
        Category(name="Healthy Living", description="Tips and advice for a healthy lifestyle"),
        Category(name="Fitness", description="Exercise routines and workout guides"),
        Category(name="Nutrition", description="Information about healthy eating and nutrition"),
        Category(name="Mental Health", description="Resources for mental wellbeing and mindfulness"),
        Category(name="Sleep", description="The importance of sleep and how to improve it"),
    ]
    session.add_all(categories)
    session.commit()
    print(f"✅ Created {len(categories)} blog categories")
    
    # Create tags
    tags = [
        Tag(name="beginner"),
        Tag(name="advanced"),
        Tag(name="quick-tips"),
        Tag(name="science-backed"),
        Tag(name="wellness"),
        Tag(name="exercise"),
        Tag(name="diet"),
        Tag(name="habits"),
        Tag(name="motivation"),
        Tag(name="health-tech"),
    ]
    session.add_all(tags)
    session.commit()
    print(f"✅ Created {len(tags)} blog tags")
    
    # Create articles
    articles = []
    for i in range(15):
        # Select random author (sometimes null for external content)
        author_id = None
        if random.random() < 0.7:  # 70% chance to have an author
            author_id = random.choice(users).id
            
        # Select random category
        category_id = random.choice(categories).id
        
        # Create article
        article = Article(
            title=fake.sentence(),
            content="\n\n".join(fake.paragraphs(nb=random.randint(3, 8))),
            author_id=author_id,
            category_id=category_id,
            source=fake.url() if not author_id else None,
            published_at=fake.date_time_between(start_date='-6M', end_date='now'),
        )
        articles.append(article)
    
    session.add_all(articles)
    session.commit()
    print(f"✅ Created {len(articles)} blog articles")
    
    # Assign tags to articles
    for article in articles:
        # Each article gets 1-4 random tags
        article_tags_count = random.randint(1, 4)
        article_tags_list = random.sample(tags, article_tags_count)
        
        article.tags.extend(article_tags_list)
    
    session.commit()
    print("✅ Assigned tags to articles")

def main():
    """Main function to generate all mock data"""
    session = SessionLocal()
    
    try:            
        # Drop and recreate all tables
        drop_tables()
        create_tables()
        
        # Generate data in the correct order to maintain relationships
        users = create_mock_users(session)
        activities = create_health_activities(session)
        user_streaks = create_user_streaks(session, users, activities)
        create_streak_completions(session, user_streaks)
        badges = create_badges(session)
        assign_user_badges(session, users, badges)
        create_blog_content(session, users)
        
        print("\n✅ All mock data generated successfully!")
        
    except Exception as e:
        print(f"❌ Error generating mock data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()


