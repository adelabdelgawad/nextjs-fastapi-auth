import asyncio
from getpass import getpass
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from db.models import Account
from routers.srv.auth import hash_password
from db.database import get_application_session


async def reset_password():
    username = input("Enter the username: ")
    new_password = getpass("Enter the new password: ")

    async for session in get_application_session():
        query = select(Account).where(Account.username == username)
        result = await session.execute(query)
        user = result.one_or_none()

        if user:
            user.password = hash_password(new_password)
            await session.commit()
            print(f"Password for user '{username}' has been updated.")
        else:
            print(f"User '{username}' not found.")


if __name__ == "__main__":
    asyncio.run(reset_password())
