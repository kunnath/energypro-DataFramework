#!/usr/bin/env python
"""
Quick Start Test - MongoDB ISTA Framework
Demonstrates test data provisioning and usage
"""

import os
from pymongo import MongoClient
import json

def test_mongodb_connection():
    """Test 1: Verify MongoDB connection"""
    print("\n" + "="*60)
    print("TEST 1: MongoDB Connection")
    print("="*60)
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("✗ MONGODB_URI environment variable not set")
        print("  Set it with: export MONGODB_URI='your-connection-string'")
        print("  Or add to .env file")
        return False
    
    client = MongoClient(mongodb_uri)
    
    try:
        # Verify connection
        client.admin.command('ping')
        print("✓ Successfully connected to MongoDB Atlas")
        
        # Get database info
        db = client.sample_mflix
        collections = db.list_collection_names()
        print(f"✓ Database: {db.name}")
        print(f"✓ Collections: {', '.join(collections)}")
        
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False
    finally:
        client.close()


def test_movies_collection():
    """Test 2: Query movies collection"""
    print("\n" + "="*60)
    print("TEST 2: Movies Collection Query")
    print("="*60)
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("✗ MONGODB_URI environment variable not set")
        return False
    
    client = MongoClient(mongodb_uri)
    
    try:
        db = client.sample_mflix
        movies = db.movies
        
        # Count documents
        count = movies.count_documents({})
        print(f"✓ Total movies in collection: {count}")
        
        # Find high-rated movies
        high_rated = movies.count_documents({"imdb.rating": {"$gte": 8.0}})
        print(f"✓ High-rated movies (IMDB >= 8.0): {high_rated}")
        
        # Get sample movie
        sample = movies.find_one({"imdb.rating": {"$gte": 8.0}})
        if sample:
            print(f"✓ Sample high-rated movie: '{sample['title']}' ({sample['year']})")
            print(f"  Rating: {sample['imdb']['rating']}/10, Votes: {sample['imdb']['votes']}")
        
        return True
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return False
    finally:
        client.close()


def test_users_collection():
    """Test 3: Query users collection"""
    print("\n" + "="*60)
    print("TEST 3: Users Collection Query")
    print("="*60)
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("✗ MONGODB_URI environment variable not set")
        return False
    
    client = MongoClient(mongodb_uri)
    
    try:
        db = client.sample_mflix
        users = db.users
        
        # Count documents
        count = users.count_documents({})
        print(f"✓ Total users in collection: {count}")
        
        # Get sample user
        sample = users.find_one({})
        if sample:
            print(f"✓ Sample user: '{sample.get('name', 'Unknown')}'")
            email = sample.get('email', 'No email')
            print(f"  Email: {email}")
        
        return True
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return False
    finally:
        client.close()


def test_data_factory():
    """Test 4: Data factory functionality"""
    print("\n" + "="*60)
    print("TEST 4: Data Factory")
    print("="*60)
    
    try:
        import sys
        sys.path.insert(0, '/Users/kunnath/Projects/Ista/test-data-automation')
        from mongo_factories import MovieFactory, UserFactory
        
        # Create test data
        movie = MovieFactory.create()
        print(f"✓ Generated movie: '{movie['title']}' ({movie['year']})")
        print(f"  Rated: {movie.get('rated', 'N/A')}, Runtime: {movie.get('runtime', 'N/A')} mins")
        
        user = UserFactory.create()
        print(f"✓ Generated user: '{user.get('name', 'Unknown')}'")
        print(f"  Email: {user.get('email', 'No email')}")
        
        # Create batch
        batch = MovieFactory.create_batch(3)
        print(f"✓ Generated batch of 3 movies: {[m['title'] for m in batch]}")
        
        return True
    except Exception as e:
        print(f"✗ Factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_adapter():
    """Test 5: Multi-database adapter"""
    print("\n" + "="*60)
    print("TEST 5: Data Adapter (Multi-Database Support)")
    print("="*60)
    
    try:
        import sys
        sys.path.insert(0, '/Users/kunnath/Projects/Ista')
        from governance.data_adapter import get_adapter
        
        # Get MongoDB adapter
        adapter = get_adapter('mongodb')
        print(f"✓ Created adapter: {adapter.__class__.__name__}")
        
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            print("✗ MONGODB_URI environment variable not set")
            print("  Set it with: export MONGODB_URI='your-connection-string'")
            print("  Or add to .env file")
            return False
        
        # Connect
        adapter.connect(mongodb_uri)
        print(f"✓ Connected to MongoDB")
        
        # Get stats
        stats = adapter.get_collection_stats('movies')
        count = stats.get('count', stats.get('documents', 0))
        size_mb = stats.get('size_mb', stats.get('size_bytes', 0) / 1024 / 1024)
        print(f"✓ Collection stats - Documents: {count}, Size: {size_mb:.2f} MB")
        
        # Query documents
        docs = adapter.find_documents('movies', {'year': {'$gte': 2020}}, limit=3)
        print(f"✓ Found {len(docs)} movies from 2020 onwards")
        
        # Disconnect
        adapter.disconnect()
        print(f"✓ Disconnected from MongoDB")
        
        return True
    except Exception as e:
        print(f"✗ Adapter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + " ISTA MongoDB Framework - Quick Start Tests ".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    # Check environment variable
    if not os.getenv("MONGODB_URI"):
        print("\n⚠️  MONGODB_URI environment variable not set!")
        print("\nTo use this test, set your MongoDB connection string:")
        print("  export MONGODB_URI='mongodb+srv://user:password@cluster.net/database'")
        print("\nOr create a .env file with:")
        print("  MONGODB_URI=mongodb+srv://user:password@cluster.net/database")
        print("\nThen run:")
        print("  source .env")
        print("  python test_mongodb_quickstart.py")
        return 1
    
    # Run tests
    results = []
    results.append(("MongoDB Connection", test_mongodb_connection()))
    results.append(("Movies Collection", test_movies_collection()))
    results.append(("Users Collection", test_users_collection()))
    results.append(("Data Factory", test_data_factory()))
    results.append(("Data Adapter", test_data_adapter()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} | {test_name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print("="*60)
    print(f"Results: {passed_count}/{total_count} tests passed\n")
    
    if passed_count == total_count:
        print("🎉 All tests passed! Your MongoDB setup is ready!")
        print("\nNext steps:")
        print("1. Read MONGODB_QUICK_START.md for detailed guide")
        print("2. Read MONGODB_REFERENCE_CARD.md for command reference")
        print("3. Read INDEX.md for complete navigation")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit(main())
