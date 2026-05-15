import asyncpg


async def get_connection():

    return await asyncpg.connect(
        user="smpp_user",
        password="smpp_pass",
        database="smpp_gateway",
        host="127.0.0.1",
        port=5432
    )
