"""
API v1 路由汇总
"""
from fastapi import APIRouter
from app.api.v1 import auth, inboxes, contacts, conversations, messages, sse, knowledge, agent, sentiment, tickets, dashboard

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router, tags=["Auth"])
router.include_router(inboxes.router, tags=["Inboxes"])
router.include_router(contacts.router, tags=["Contacts"])
router.include_router(conversations.router, tags=["Conversations"])
router.include_router(messages.router, tags=["Messages"])
router.include_router(sse.router, tags=["SSE"])
router.include_router(knowledge.router, tags=["Knowledge"])
router.include_router(agent.router, tags=["Agent"])
router.include_router(sentiment.router, tags=["Sentiment"])
router.include_router(tickets.router, tags=["Tickets"])
router.include_router(dashboard.router, tags=["Dashboard"])
