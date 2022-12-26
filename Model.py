class User:
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def save(self):
        db.users.insert_one({'email': self.email, 'password': self.password})