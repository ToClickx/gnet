import os
import json
from user.account import User

USERS_DIR = os.path.join(os.path.dirname(__file__), '..', 'users')

if not os.path.exists(USERS_DIR):
    os.makedirs(USERS_DIR)


def user_folder_path(username: str) -> str:
    return os.path.join(USERS_DIR, username)


def user_data_path(username: str) -> str:
    return os.path.join(user_folder_path(username), 'data.json')


def user_transaction_log_path(username: str) -> str:
    return os.path.join(user_folder_path(username), 'transactions.json')


def user_debit_cards_path(username: str) -> str:
    return os.path.join(user_folder_path(username), 'debit_cards.json')


def save_user(user: User) -> None:
    folder = user_folder_path(user.username)
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Save core data (excluding debit cards and transactions)
    core_data = {
        "username": user.username,
        "password_hash": user.password_hash,
        "gBalance": user.gBalance,
        "app_data": user.app_data,
    }
    with open(user_data_path(user.username), 'w', encoding='utf-8') as f:
        json.dump(core_data, f, indent=4)

    # Save debit cards
    with open(user_debit_cards_path(user.username), 'w', encoding='utf-8') as f:
        json.dump(user.debit_cards, f, indent=4)

    # Save transaction log
    with open(user_transaction_log_path(user.username), 'w', encoding='utf-8') as f:
        json.dump(user.transaction_log, f, indent=4)


def load_user(username: str) -> User | None:
    data_path = user_data_path(username)
    debit_path = user_debit_cards_path(username)
    transactions_path = user_transaction_log_path(username)

    if not os.path.isfile(data_path):
        return None

    with open(data_path, 'r', encoding='utf-8') as f:
        core_data = json.load(f)

    debit_cards = {}
    if os.path.isfile(debit_path):
        with open(debit_path, 'r', encoding='utf-8') as f:
            debit_cards = json.load(f)

    transaction_log = []
    if os.path.isfile(transactions_path):
        with open(transactions_path, 'r', encoding='utf-8') as f:
            transaction_log = json.load(f)

    # Merge everything into user data dict
    full_data = core_data
    full_data["debit_cards"] = debit_cards
    full_data["transaction_log"] = transaction_log

    return User(username=None, data=full_data)


def load_all_users() -> dict[str, User]:
    users = {}
    for username in os.listdir(USERS_DIR):
        folder = user_folder_path(username)
        if os.path.isdir(folder):
            user = load_user(username)
            if user:
                users[username] = user
    return users


def delete_user(username: str) -> None:
    folder = user_folder_path(username)
    if os.path.isdir(folder):
        for filename in os.listdir(folder):
            os.remove(os.path.join(folder, filename))
        os.rmdir(folder)
