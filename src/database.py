import json
from typing import List, Dict, Any
import constants as c
import bcrypt


# Hash a password using bcrypt
def hash_password(password):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    # Convert the hashed password from bytes to a string
    return hashed_password.decode('utf-8')


def load_db() -> List[Dict[str, Any]]:
    """
    Load a JSON file and store its contents in memory as a list.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing the database.
    """
    try:
        with open(c.DB_FILE, 'r') as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
            else:
                raise ValueError("JSON file does not contain a list")
    except Exception as e:
        print(f"Error loading database: {e}")
        return []


def _save_db(data: List[Dict[str, Any]]) -> None:
    """
    Save the in-memory database (a list) to a JSON file.

    Args:
        data (List[Dict[str, Any]]): The list of dictionaries to be saved.
    """
    try:
        with open(c.DB_FILE, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Database successfully saved to {c.DB_FILE}")
    except Exception as e:
        print(f"Error saving database: {e}")


def add_new_user(username: str, full_name: str, email: str, password: str) -> None:
    """
    Add a new user to the database with the password hashed and disabled set to True.

    Args:
        username (str): The username of the new user.
        full_name (str): The full name of the new user.
        email (str): The email address of the new user.
        password (str): The plain text password of the new user.

    Raises:
        ValueError: If the username already exists in the database.
    """

    # Load the current database
    db: List[Dict] = load_db()

    # Check if the user already exists
    for user in db:
        if user['username'] == username:
            raise ValueError(f"User '{username}' already exists.")

    # Hash the password
    hashed_password = hash_password(password)

    # Create the new user entry
    new_user = {
        "id": len(db) + 1,  # Auto-increment ID based on list length
        "username": username,
        "full_name": full_name,
        "email": email,
        "hashed_password": hashed_password,
        "is_active": False  # New users are disabled by default
    }

    # Add the new user to the database
    db.append(new_user)

    # Save the updated database
    _save_db(db)

    print(f"New user '{username}' added and saved to database.")