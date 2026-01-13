"""
MongoDB Data Factories for sample_mflix collections

Provides factory classes to generate realistic test data for MongoDB
collections matching the sample_mflix schema structure.
"""

from faker import Faker
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

fake = Faker()


class BaseFactory:
    """Base factory for generating MongoDB documents"""
    
    collection_name: str = "base"
    
    @classmethod
    def create(cls, **overrides) -> Dict[str, Any]:
        """Create a single document with optional field overrides"""
        doc = cls.build(**overrides)
        return doc
    
    @classmethod
    def create_batch(cls, count: int, **overrides) -> List[Dict[str, Any]]:
        """Create multiple documents"""
        return [cls.create(**overrides) for _ in range(count)]
    
    @classmethod
    def build(cls, **overrides) -> Dict[str, Any]:
        """Build document dictionary (override in subclasses)"""
        raise NotImplementedError()


class MovieFactory(BaseFactory):
    """Factory for generating movie documents"""
    
    collection_name = "movies"
    
    GENRES = ["Action", "Adventure", "Comedy", "Crime", "Drama", "Fantasy",
              "Horror", "Thriller", "Romance", "Sci-Fi", "Animation", "Documentary"]
    
    RATINGS = ["G", "PG", "PG-13", "R", "NC-17", "Not Rated"]
    
    @classmethod
    def build(cls, **overrides) -> Dict[str, Any]:
        """Build a movie document"""
        
        movie = {
            "_id": overrides.get("_id", ObjectId()),
            "title": overrides.get("title", fake.sentence(nb_words=3).rstrip('.')),
            "year": overrides.get("year", fake.random_int(min=1900, max=2024)),
            "rated": overrides.get("rated", fake.random_element(cls.RATINGS)),
            "runtime": overrides.get("runtime", fake.random_int(min=80, max=240)),
            "genres": overrides.get("genres", fake.random_sample(
                elements=cls.GENRES, 
                length=fake.random_int(min=1, max=3)
            )),
            "director": overrides.get("director", fake.name()),
            "writers": overrides.get("writers", [fake.name() for _ in range(
                fake.random_int(min=1, max=3)
            )]),
            "cast": overrides.get("cast", [fake.name() for _ in range(
                fake.random_int(min=1, max=8)
            )]),
            "plot": overrides.get("plot", fake.text(max_nb_chars=200)),
            "fullplot": overrides.get("fullplot", fake.text(max_nb_chars=500)),
            "languages": overrides.get("languages", 
                                      fake.random_sample(
                                          elements=["English", "Spanish", "French", "German"],
                                          length=1
                                      )),
            "countries": overrides.get("countries", 
                                      fake.random_sample(
                                          elements=["USA", "UK", "France", "Germany", "Japan"],
                                          length=1
                                      )),
            "type": overrides.get("type", "movie"),
            "released": overrides.get("released", 
                                     datetime(
                                         year=fake.random_int(min=1900, max=2024),
                                         month=fake.random_int(min=1, max=12),
                                         day=fake.random_int(min=1, max=28)
                                     )),
            "imdb": overrides.get("imdb", {
                "rating": round(fake.pyfloat(min_value=1, max_value=10), 1),
                "votes": fake.random_int(min=1000, max=2000000),
                "id": fake.random_int(min=100000, max=10000000)
            }),
            "tomatoes": overrides.get("tomatoes", {
                "viewer": {
                    "rating": round(fake.pyfloat(min_value=1, max_value=10), 1),
                    "numReviews": fake.random_int(min=100, max=10000)
                },
                "lastUpdated": datetime.now()
            }),
            "awards": overrides.get("awards", {
                "wins": fake.random_int(min=0, max=20),
                "nominations": fake.random_int(min=0, max=50)
            }),
            "poster": overrides.get("poster", fake.url()),
            "metacritic": overrides.get("metacritic", fake.random_int(min=0, max=100))
        }
        
        return movie


class UserFactory(BaseFactory):
    """Factory for generating user documents"""
    
    collection_name = "users"
    
    @classmethod
    def build(cls, **overrides) -> Dict[str, Any]:
        """Build a user document"""
        
        # Pre-generate a movie list to reference
        movie_ids = [ObjectId() for _ in range(random.randint(0, 10))]
        
        user = {
            "_id": overrides.get("_id", ObjectId()),
            "username": overrides.get("username", fake.user_name()),
            "email": overrides.get("email", fake.email()),
            "password_hash": overrides.get("password_hash", fake.sha256()),
            "profile": overrides.get("profile", {
                "name": fake.name(),
                "bio": fake.text(max_nb_chars=100),
                "avatar_url": fake.url(),
                "created_at": datetime.now() - timedelta(days=fake.random_int(min=1, max=365))
            }),
            "favorite_movies": overrides.get("favorite_movies", movie_ids),
            "watch_history": overrides.get("watch_history", [
                {
                    "movie_id": ObjectId(),
                    "watched_at": datetime.now() - timedelta(days=fake.random_int(min=0, max=30)),
                    "rating": fake.random_int(min=1, max=10),
                    "is_completed": fake.pybool()
                }
                for _ in range(random.randint(0, 5))
            ]),
            "preferences": overrides.get("preferences", {
                "genres": fake.random_sample(
                    elements=["Action", "Drama", "Thriller", "Comedy", "Horror"],
                    length=random.randint(1, 3)
                ),
                "language": fake.random_element(["en", "es", "fr", "de"]),
                "notifications_enabled": fake.pybool(),
                "theme": fake.random_element(["light", "dark"])
            }),
            "subscription": overrides.get("subscription", {
                "plan": fake.random_element(["free", "basic", "premium"]),
                "active": fake.pybool(),
                "expires_at": datetime.now() + timedelta(days=fake.random_int(min=0, max=365))
            }),
            "created_at": overrides.get("created_at", 
                                       datetime.now() - timedelta(days=fake.random_int(min=1, max=365))),
            "updated_at": overrides.get("updated_at", datetime.now())
        }
        
        return user


class CommentFactory(BaseFactory):
    """Factory for generating comment documents"""
    
    collection_name = "comments"
    
    @classmethod
    def build(cls, **overrides) -> Dict[str, Any]:
        """Build a comment document"""
        
        comment = {
            "_id": overrides.get("_id", ObjectId()),
            "movie_id": overrides.get("movie_id", ObjectId()),
            "user_id": overrides.get("user_id", ObjectId()),
            "email": overrides.get("email", fake.email()),
            "text": overrides.get("text", fake.text(max_nb_chars=500)),
            "date": overrides.get("date", datetime.now() - timedelta(days=fake.random_int(min=0, max=365))),
            "likes": overrides.get("likes", fake.random_int(min=0, max=1000)),
            "is_hidden": overrides.get("is_hidden", fake.pybool(truth_percentage=5)),
            "rating": overrides.get("rating", fake.random_int(min=1, max=10)),
            "replies": overrides.get("replies", [
                {
                    "_id": ObjectId(),
                    "user_id": ObjectId(),
                    "email": fake.email(),
                    "text": fake.text(max_nb_chars=200),
                    "date": datetime.now() - timedelta(days=fake.random_int(min=0, max=30)),
                    "likes": fake.random_int(min=0, max=100)
                }
                for _ in range(random.randint(0, 3))
            ])
        }
        
        return comment


class SessionFactory(BaseFactory):
    """Factory for generating session documents"""
    
    collection_name = "sessions"
    
    @classmethod
    def build(cls, **overrides) -> Dict[str, Any]:
        """Build a session document"""
        
        created_at = datetime.now() - timedelta(hours=fake.random_int(min=0, max=24))
        expires_at = created_at + timedelta(hours=24)
        
        session = {
            "_id": overrides.get("_id", ObjectId()),
            "user_id": overrides.get("user_id", ObjectId()),
            "token": overrides.get("token", fake.sha256()),
            "refresh_token": overrides.get("refresh_token", fake.sha256()),
            "created_at": overrides.get("created_at", created_at),
            "expires_at": overrides.get("expires_at", expires_at),
            "last_activity": overrides.get("last_activity", 
                                          created_at + timedelta(hours=fake.random_int(min=0, max=24))),
            "ip_address": overrides.get("ip_address", fake.ipv4()),
            "user_agent": overrides.get("user_agent", fake.user_agent()),
            "device_info": overrides.get("device_info", {
                "type": fake.random_element(["web", "mobile", "tablet"]),
                "os": fake.random_element(["Windows", "macOS", "Linux", "iOS", "Android"]),
                "browser": fake.random_element(["Chrome", "Firefox", "Safari", "Edge"])
            }),
            "is_active": overrides.get("is_active", fake.pybool(truth_percentage=80))
        }
        
        return session


# Example usage functions
def create_movie_dataset(count: int = 100) -> List[Dict[str, Any]]:
    """Create test dataset of movies"""
    return MovieFactory.create_batch(count)


def create_user_dataset(count: int = 50) -> List[Dict[str, Any]]:
    """Create test dataset of users"""
    return UserFactory.create_batch(count)


def create_comment_dataset(count: int = 200, movie_ids: Optional[List[ObjectId]] = None,
                          user_ids: Optional[List[ObjectId]] = None) -> List[Dict[str, Any]]:
    """Create test dataset of comments with references"""
    comments = []
    
    for _ in range(count):
        comment = CommentFactory.create(
            movie_id=random.choice(movie_ids) if movie_ids else ObjectId(),
            user_id=random.choice(user_ids) if user_ids else ObjectId()
        )
        comments.append(comment)
    
    return comments


def create_session_dataset(count: int = 100, user_ids: Optional[List[ObjectId]] = None) -> List[Dict[str, Any]]:
    """Create test dataset of sessions"""
    sessions = []
    
    for _ in range(count):
        session = SessionFactory.create(
            user_id=random.choice(user_ids) if user_ids else ObjectId()
        )
        sessions.append(session)
    
    return sessions


# Advanced factory methods for specific test scenarios

class MovieFactoryVariants:
    """Variants of movie factory for specific test scenarios"""
    
    @staticmethod
    def create_classic_movie(**overrides) -> Dict[str, Any]:
        """Create a classic movie (pre-1980)"""
        return MovieFactory.create(
            year=fake.random_int(min=1900, max=1979),
            **overrides
        )
    
    @staticmethod
    def create_modern_movie(**overrides) -> Dict[str, Any]:
        """Create a modern movie (2000-2024)"""
        return MovieFactory.create(
            year=fake.random_int(min=2000, max=2024),
            **overrides
        )
    
    @staticmethod
    def create_high_rated_movie(**overrides) -> Dict[str, Any]:
        """Create a highly rated movie (IMDB > 8.0)"""
        return MovieFactory.create(
            imdb={
                "rating": round(fake.pyfloat(min_value=8.0, max_value=10.0), 1),
                "votes": fake.random_int(min=50000, max=2000000),
                "id": fake.random_int(min=100000, max=10000000)
            },
            **overrides
        )
    
    @staticmethod
    def create_movie_batch_with_genres(count: int, genres: List[str], **overrides) -> List[Dict[str, Any]]:
        """Create movies with specific genres"""
        movies = []
        for _ in range(count):
            movies.append(MovieFactory.create(
                genres=genres,
                **overrides
            ))
        return movies


class UserFactoryVariants:
    """Variants of user factory for specific test scenarios"""
    
    @staticmethod
    def create_premium_user(**overrides) -> Dict[str, Any]:
        """Create a premium subscription user"""
        return UserFactory.create(
            subscription={
                "plan": "premium",
                "active": True,
                "expires_at": datetime.now() + timedelta(days=365)
            },
            **overrides
        )
    
    @staticmethod
    def create_new_user(**overrides) -> Dict[str, Any]:
        """Create a newly registered user (created in last 7 days)"""
        return UserFactory.create(
            profile={
                "name": fake.name(),
                "bio": fake.text(max_nb_chars=100),
                "avatar_url": fake.url(),
                "created_at": datetime.now() - timedelta(days=fake.random_int(min=0, max=7))
            },
            **overrides
        )
    
    @staticmethod
    def create_active_user(min_watches: int = 5, **overrides) -> Dict[str, Any]:
        """Create an active user with watch history"""
        return UserFactory.create(
            watch_history=[
                {
                    "movie_id": ObjectId(),
                    "watched_at": datetime.now() - timedelta(days=fake.random_int(min=0, max=30)),
                    "rating": fake.random_int(min=1, max=10),
                    "is_completed": True
                }
                for _ in range(min_watches)
            ],
            **overrides
        )


if __name__ == "__main__":
    # Example usage
    print("Generating sample_mflix test data...")
    
    # Create movies
    movies = MovieFactory.create_batch(5)
    movie_ids = [movie['_id'] for movie in movies]
    print(f"Created {len(movies)} movies")
    
    # Create users
    users = UserFactory.create_batch(3)
    user_ids = [user['_id'] for user in users]
    print(f"Created {len(users)} users")
    
    # Create comments with references
    comments = create_comment_dataset(10, movie_ids=movie_ids, user_ids=user_ids)
    print(f"Created {len(comments)} comments")
    
    # Create sessions
    sessions = SessionFactory.create_batch(5)
    print(f"Created {len(sessions)} sessions")
    
    print("\nExample movie:")
    import json
    print(json.dumps(movies[0], indent=2, default=str))
