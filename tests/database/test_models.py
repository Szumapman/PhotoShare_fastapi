import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import (
    Base,
    Photo,
    User,
    Tag,
    Comment,
    Rating,
    RefreshToken,
    LogoutAccessToken,
)


class TestDatabaseModels(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

    def test_photo_model(self):
        user = User(username="testuser", email="test@example.com", password="password")
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        photo = Photo(
            user_id=user.id,
            photo_url="http://example.com/photo.jpg",
            description="Test photo",
        )
        self.session.add(photo)
        self.session.commit()

        retrieved_photo = self.session.query(Photo).filter_by(id=photo.id).first()
        self.assertIsNotNone(retrieved_photo)
        self.assertEqual(retrieved_photo.photo_url, "http://example.com/photo.jpg")
        self.assertEqual(retrieved_photo.description, "Test photo")
        self.assertEqual(retrieved_photo.user_id, user.id)

    def test_user_model(self):
        user = User(username="testuser", email="test@example.com", password="password")
        self.session.add(user)
        self.session.commit()

        retrieved_user = self.session.query(User).filter_by(username="testuser").first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.email, "test@example.com")
        self.assertTrue(retrieved_user.is_active)

    def test_tag_model(self):
        tag = Tag(name="testtag")
        self.session.add(tag)
        self.session.commit()

        retrieved_tag = self.session.query(Tag).filter_by(name="testtag").first()
        self.assertIsNotNone(retrieved_tag)
        self.assertEqual(retrieved_tag.name, "testtag")

    def test_comment_model(self):
        user = User(username="testuser", email="test@example.com", password="password")
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        photo = Photo(user_id=user.id, photo_url="http://example.com/photo.jpg")
        self.session.add(photo)
        self.session.commit()

        comment = Comment(photo_id=photo.id, user_id=user.id, content="Test comment")
        self.session.add(comment)
        self.session.commit()

        retrieved_comment = self.session.query(Comment).filter_by(id=comment.id).first()
        self.assertIsNotNone(retrieved_comment)
        self.assertEqual(retrieved_comment.content, "Test comment")
        self.assertEqual(retrieved_comment.photo_id, photo.id)
        self.assertEqual(retrieved_comment.user_id, user.id)

    def test_rating_model(self):
        user = User(username="testuser", email="test@example.com", password="password")
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        photo = Photo(user_id=user.id, photo_url="http://example.com/photo.jpg")
        self.session.add(photo)
        self.session.commit()

        rating = Rating(photo_id=photo.id, user_id=user.id, score=5)
        self.session.add(rating)
        self.session.commit()

        retrieved_rating = self.session.query(Rating).filter_by(id=rating.id).first()
        self.assertIsNotNone(retrieved_rating)
        self.assertEqual(retrieved_rating.score, 5)
        self.assertEqual(retrieved_rating.photo_id, photo.id)
        self.assertEqual(retrieved_rating.user_id, user.id)

    def test_refresh_token_model(self):
        user = User(username="testuser", email="test@example.com", password="password")
        self.session.add(user)
        self.session.commit()

        refresh_token = RefreshToken(
            refresh_token="testtoken",
            user_id=user.id,
            session_id="testsession",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        self.session.add(refresh_token)
        self.session.commit()

        retrieved_token = (
            self.session.query(RefreshToken)
            .filter_by(refresh_token="testtoken")
            .first()
        )
        self.assertIsNotNone(retrieved_token)
        self.assertEqual(retrieved_token.user_id, user.id)
        self.assertEqual(retrieved_token.session_id, "testsession")

    def test_logout_access_token_model(self):
        logout_token = LogoutAccessToken(
            logout_access_token="testlogouttoken",
            expires_at=datetime.utcnow() + timedelta(minutes=15),
        )
        self.session.add(logout_token)
        self.session.commit()

        retrieved_token = (
            self.session.query(LogoutAccessToken)
            .filter_by(logout_access_token="testlogouttoken")
            .first()
        )
        self.assertIsNotNone(retrieved_token)
        self.assertTrue(retrieved_token.expires_at > datetime.utcnow())

    def test_photo_average_rating(self):
        user = User(username="testuser", email="test@example.com", password="password")
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        photo = Photo(user_id=user.id, photo_url="http://example.com/photo.jpg")
        self.session.add(photo)
        self.session.commit()

        rating1 = Rating(photo_id=photo.id, user_id=user.id, score=4)
        rating2 = Rating(photo_id=photo.id, user_id=user.id, score=5)
        self.session.add_all([rating1, rating2])
        self.session.commit()

        retrieved_photo = self.session.query(Photo).filter_by(id=photo.id).first()
        self.assertEqual(retrieved_photo.average_rating, 4.5)

    def test_photo_no_ratings(self):
        user = User(username="testuser", email="test@example.com", password="password")
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        photo = Photo(user_id=user.id, photo_url="http://example.com/photo.jpg")
        self.session.add(photo)
        self.session.commit()

        retrieved_photo = self.session.query(Photo).filter_by(id=photo.id).first()
        self.assertIsNone(retrieved_photo.average_rating)


if __name__ == "__main__":
    unittest.main()
