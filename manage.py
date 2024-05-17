import asyncio
import re
import argparse
import sys
from datetime import datetime

from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt
from validator_collection import validators

from src.database.db import SessionLocal
from src.database.dependencies import get_avatar_provider
from src.database.models import User, RefreshToken, LogoutAccessToken
from src.services.pasword import get_password_hash
from src.conf.constant import MAX_USERNAME_LENGTH, ROLE_ADMIN


class UserNameValidator(Validator):
    def validate(self, document):
        text = document.text
        if len(text) > MAX_USERNAME_LENGTH:
            raise ValidationError(
                message=f"Username must be less than {MAX_USERNAME_LENGTH} characters long."
            )
        if len(text) < 3:
            raise ValidationError(
                message=f"Username must be at least 3 characters long."
            )


class PasswordValidator(Validator):
    def validate(self, document):
        text = document.text
        if len(text) > 45:
            raise ValidationError(
                message=f"Password must be less than 45 characters long."
            )
        elif len(text) < 8:
            raise ValidationError(
                message=f"Password must be at least 8 characters long."
            )
        elif not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*\W).{8,45}$", text):
            raise ValidationError(
                message="Password must contain at least one uppercase and lowercase letter, one digit and one special character"
            )


def __get_data():
    print("Create a new admin user. ")
    username = prompt("username: ", validator=UserNameValidator())
    while True:
        try:
            email = validators.email(prompt("email: "))
        except ValueError as e:
            print(e)
            continue
        break
    while True:
        password1 = prompt(
            "password: ", is_password=True, validator=PasswordValidator()
        )
        password2 = prompt(
            "retype password: ", is_password=True, validator=PasswordValidator()
        )
        if password1 != password2:
            print("Passwords do not match. Try again.")
            continue
        break

    return username, email, password1


async def __add_admin_to_db(username, email, password):
    avatar_provider = get_avatar_provider()
    avatar = avatar_provider.get_avatar(email, 255)
    db = SessionLocal()
    user = User(
        username=username,
        email=email,
        password=get_password_hash(password),
        avatar=avatar,
        role=ROLE_ADMIN,
    )
    db.add(user)
    db.commit()


async def __delete_exp_tokens(token_type: str):
    if token_type == "refresh_token":
        token_to_clean = RefreshToken
    elif token_type == "access_token":
        token_to_clean = LogoutAccessToken
    else:
        raise ValueError("token_type must be either 'refresh_token' or 'access_token'")
    db = SessionLocal()
    tokens_to_delete = (
        db.query(token_to_clean)
        .filter(token_to_clean.expires_at < datetime.utcnow())
        .all()
    )
    for token in tokens_to_delete:
        db.delete(token)
    db.commit()


def create_admin():
    while True:
        try:
            username, email, password = __get_data()
            asyncio.run(__add_admin_to_db(username, email, password))
        except Exception as e:
            print(e)
            print("Try again.")
            continue
        break
    print("Admin user created.")


def clean_access_tokens():
    try:
        asyncio.run(__delete_exp_tokens("access_token"))
    except Exception as e:
        print(e)


def clean_refresh_tokens():
    try:
        asyncio.run(__delete_exp_tokens("refresh_token"))
    except Exception as e:
        print(e)


CALLABLE_FUNCTIONS = {
    "create_admin": create_admin,
    "clean_access_tokens": clean_access_tokens,
    "clean_refresh_tokens": clean_refresh_tokens,
}


def __parse_arg():
    parser = argparse.ArgumentParser(
        description="Launch the manage.py file with the name of the function you want to use as an argument."
    )
    parser.add_argument(
        "function",
        help=f"The name of the function you want to run. You can use: {', '.join(CALLABLE_FUNCTIONS)}",
    )
    args = parser.parse_args()
    if args.function not in CALLABLE_FUNCTIONS:
        print(
            "Invalid function. Please use one of the following functions as an argument:\n",
            "\n".join(CALLABLE_FUNCTIONS),
        )
        sys.exit(1)
    return args.function


if __name__ == "__main__":
    arg = __parse_arg()
    cmd = CALLABLE_FUNCTIONS[arg]
    cmd()
