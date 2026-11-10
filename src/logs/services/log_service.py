from datetime import datetime, timedelta

from sqlalchemy import func, select
from src.database.mysql_connector import get_db
from src.logs.models.log import ActionType, Log, LogTypes


async def create_log(user_id: str, action: ActionType=ActionType.LOGIN, type: LogTypes=LogTypes.INFO, description: str=None):
    async with get_db() as session:
        log = Log(user_id=user_id, action=action, description=description, type=type)
        session.add(log)
        await session.commit()
    return log

async def create_log_from_exception(user_id: str, exception: Exception, action: ActionType=ActionType.LOGIN):
    async with get_db() as session:
        log = Log(user_id=user_id, action=action, description=str(exception), type=LogTypes.ERR)
        session.add(log)
        await session.commit()
    return log

async def count_login_last_months(user_id: str):
    async with get_db() as session:
        query = select(func.count()).where(Log.user_id == user_id, Log.action == ActionType.LOGIN, Log.created_at > datetime.now() - timedelta(days=30))
        result = await session.execute(query)
        return result.scalar()
    
async def count_users_login_last_months():
    async with get_db() as session:
        query = select(Log.user_id, func.count()).where(Log.action == ActionType.LOGIN, Log.type == LogTypes.INFO, Log.created_at > datetime.now() - timedelta(days=30)).group_by(Log.user_id)
        result = await session.execute(query)
        res = result.fetchall()
        gen= {user_id: count for user_id, count in res}
        print(gen)
        return gen
    

