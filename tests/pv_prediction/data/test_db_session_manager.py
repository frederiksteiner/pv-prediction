import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from pv_prediction.data.db_session_manger import DBSessionManager

# pylint:disable=protected-access


class TestDBSessionManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite:///:memory:")
        DBSessionManager.engine = cls.engine
        DBSessionManager._session_maker = sessionmaker(bind=cls.engine)

    def setUp(self) -> None:
        self.session_manager = DBSessionManager()

    def test_singleton_behavior(self) -> None:
        another_session_manager = DBSessionManager()
        self.assertIs(self.session_manager, another_session_manager)

    def test_get_session(self) -> None:
        session1 = DBSessionManager.get_session()
        self.assertIsInstance(session1, Session)

        # Retrieve another session
        session2 = DBSessionManager.get_session()
        self.assertIsNot(session1, session2)

    def test_release_session(self) -> None:
        session = DBSessionManager.get_session()
        self.assertIsInstance(session, Session)

        DBSessionManager.release_session(session)

        session2 = DBSessionManager.get_session()
        self.assertIs(session, session2)

    def test_close_sessions(self) -> None:
        session1 = DBSessionManager.get_session()
        session2 = DBSessionManager.get_session()
        self.assertNotEqual(session1, session2)

        # Close all sessions
        DBSessionManager.close_sessions()

        # Check that the pool is empty now
        self.assertEqual(DBSessionManager._session_pool.qsize(), 0)
