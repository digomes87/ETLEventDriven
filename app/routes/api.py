import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.repositories.events import SqlAlchemyEventRepository
from app.schemas. # nao tenho ainda schemas !!!!