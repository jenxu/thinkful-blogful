import os
import unittest
from urllib.parse import urlparse

from werkzeug.security import generate_password_hash

# Configure your app to use the testing database
os.environ["CONFIG_PATH"] = "blog.config.TestingConfig"

from blog import app
from blog.database import Base, engine, session, User, Entry

class TestViews(unittest.TestCase):
    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create an example user
        self.user = User(name="Alice", email="alice@example.com",
                         password=generate_password_hash("test"))
        session.add(self.user)
        session.commit()

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)
        
    def simulate_login(self):
        with self.client.session_transaction() as http_session:
            http_session["user_id"] = str(self.user.id)
            http_session["_fresh"] = True

    def test_add_entry(self):
        self.simulate_login()

        response = self.client.post("/entry/add", data={
            "title": "Test Entry",
            "content": "Test content"
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, "/")
        entries = session.query(Entry).all()
        self.assertEqual(len(entries), 1)

        entry = entries[0]
        self.assertEqual(entry.title, "Test Entry")
        self.assertEqual(entry.content, "Test content")
        self.assertEqual(entry.author, self.user)
        
    def test_loggedout_add_entry(self):
        response = self.client.post("/entry/add")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, "/login")

    def test_edit_entry(self):
        self.simulate_login()
        
        response = self.client.post("/entry/add", data={
            "title": "Test Entry",
            "content": "Test content"
        })

        entries = session.query(Entry).all()
        entry=entries[0]
        
        response = self.client.post("/entry/{}/edit".format(entry.id), data={
            "content": "Updated test content"
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, "/")
        self.assertEqual(entry.title, "Test Entry")
        self.assertEqual(entry.content, "Updated test content")
        self.assertEqual(entry.author, self.user)
        
    def test_unauthorized_edit_entry(self):
        response = self.client.post("/entry/{}/edit".format(1))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, "/login")
        
    def test_delete_entry(self):
        self.simulate_login()
        
        response = self.client.post("/entry/add", data={
            "title": "Test Entry",
            "content": "Test content"
        })

        entries = session.query(Entry).all()
        entry=entries[0]
        
        response = self.client.post("/entry/{}/delete".format(entry.id))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, "/")
        entries = session.query(Entry).all()
        self.assertEqual(len(entries), 0)
        
    def test_unauthorized_delete_entry(self):
        response = self.client.post("/entry/{}/delete".format(1))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, "/login")

if __name__ == "__main__":
    unittest.main()