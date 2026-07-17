"""
种子数据脚本 — 插入测试用数据
使用方法: python -m scripts.seed
"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# 需要在运行前安装依赖
import sys
sys.path.insert(0, ".")

from app.core.database import engine
from app.core.security import hash_password
from app.models import (
    User, Inbox, Contact, ContactInbox,
    Conversation, Message, Product, Order, KnowledgeChunk
)


async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def uid() -> str:
    return str(uuid.uuid4())


async def seed():
    async with async_session() as db:
        now = datetime.now(timezone.utc)

        # ========== Users ==========
        admin_id = uid()
        agent1_id = uid()
        agent2_id = uid()

        users = [
            User(id=admin_id, email="admin@smartcs.com", hashed_password=hash_password("admin123"),
                 display_name="管理员", role="admin", availability="online"),
            User(id=agent1_id, email="agent1@smartcs.com", hashed_password=hash_password("agent123"),
                 display_name="客服小王", role="agent", availability="online"),
            User(id=agent2_id, email="agent2@smartcs.com", hashed_password=hash_password("agent123"),
                 display_name="客服小李", role="agent", availability="offline"),
        ]
        db.add_all(users)
        print(f"  ✓ Created {len(users)} users")

        # ========== Inboxes ==========
        web_inbox_id = uid()

        inboxes = [
            Inbox(id=web_inbox_id, name="网页客服", channel_type="web_widget",
                  channel_config={"widget_color": "#1890ff", "greeting": "您好！我是智能客服助手，有什么可以帮您的？"},
                  auto_assignment_enabled=True),
        ]
        db.add_all(inboxes)
        print(f"  + Created {len(inboxes)} inbox(es)")

        # ========== Contacts ==========
        contact1_id = uid()
        contact2_id = uid()
        contact3_id = uid()

        contacts = [
            Contact(id=contact1_id, name="张三", email="zhangsan@example.com", phone="13800001001",
                    reputation_score=0.95, custom_attributes={"tags": ["VIP", "老客户"]},
                    last_activity_at=now),
            Contact(id=contact2_id, name="李四", email="lisi@example.com", phone="13800001002",
                    reputation_score=0.80, custom_attributes={"tags": ["新客户"]},
                    last_activity_at=now),
            Contact(id=contact3_id, name="王五", email="wangwu@example.com", phone="13800001003",
                    reputation_score=0.45, custom_attributes={"tags": ["高退款风险"]},
                    last_activity_at=now - timedelta(days=30)),
        ]
        db.add_all(contacts)
        print(f"  ✓ Created {len(contacts)} contacts")

        # ========== ContactInboxes ==========
        cinbox1 = ContactInbox(contact_id=contact1_id, inbox_id=web_inbox_id,
                                source_id=str(uuid.uuid4()), pubsub_token=str(uuid.uuid4()))
        cinbox2 = ContactInbox(contact_id=contact2_id, inbox_id=web_inbox_id,
                                source_id=str(uuid.uuid4()), pubsub_token=str(uuid.uuid4()))
        db.add_all([cinbox1, cinbox2])
        print(f"  ✓ Created 2 contact_inboxes")

        # ========== Products ==========
        prod1_id = uid()
        prod2_id = uid()
        prod3_id = uid()

        products = [
            Product(id=prod1_id, sku="SKU-001", name="经典款纯棉T恤", description="100%纯棉，舒适透气",
                    category="服装", price=99.00,
                    specs={"color": ["白色", "黑色", "灰色"], "size": ["S", "M", "L", "XL", "XXL"]},
                    size_chart=[
                        {"height_cm_min": 160, "height_cm_max": 170, "weight_kg_min": 50, "weight_kg_max": 60, "size": "S"},
                        {"height_cm_min": 165, "height_cm_max": 175, "weight_kg_min": 55, "weight_kg_max": 70, "size": "M"},
                        {"height_cm_min": 170, "height_cm_max": 180, "weight_kg_min": 65, "weight_kg_max": 80, "size": "L"},
                        {"height_cm_min": 175, "height_cm_max": 185, "weight_kg_min": 75, "weight_kg_max": 90, "size": "XL"},
                        {"height_cm_min": 180, "height_cm_max": 195, "weight_kg_min": 85, "weight_kg_max": 105, "size": "XXL"},
                    ],
                    stock=500, image_urls=["https://example.com/images/sku001.jpg"]),
            Product(id=prod2_id, sku="SKU-002", name="运动跑鞋 Air Boost", description="轻量缓震，适合日常跑步",
                    category="鞋类", price=499.00,
                    specs={"color": ["黑白", "蓝白", "全黑"], "size": ["38", "39", "40", "41", "42", "43", "44"]},
                    stock=200, image_urls=["https://example.com/images/sku002.jpg"]),
            Product(id=prod3_id, sku="SKU-003", name="蓝牙降噪耳机 Pro", description="ANC主动降噪，40小时续航",
                    category="数码", price=299.00,
                    specs={"color": ["黑色", "白色", "蓝色"], "version": ["标准版", "Pro版"]},
                    stock=150, image_urls=["https://example.com/images/sku003.jpg"]),
        ]
        db.add_all(products)
        print(f"  ✓ Created {len(products)} products")

        # ========== Orders ==========
        orders = [
            Order(id=uid(), order_no="ORD-20260714001", contact_id=contact1_id,
                  product_name="经典款纯棉T恤", quantity=2, total_amount=198.00,
                  status="delivered", payment_status="paid",
                  shipping_address={"province": "北京市", "city": "北京市", "district": "朝阳区", "detail": "xxx路100号"},
                  logistics_no="SF1234567890", logistics_status="已签收",
                  shipped_at=now - timedelta(days=3)),
            Order(id=uid(), order_no="ORD-20260714002", contact_id=contact1_id,
                  product_name="运动跑鞋 Air Boost", quantity=1, total_amount=499.00,
                  status="shipped", payment_status="paid",
                  shipping_address={"province": "北京市", "city": "北京市", "district": "朝阳区", "detail": "xxx路100号"},
                  logistics_no="SF1234567891", logistics_status="运输中，预计7月16日到达",
                  shipped_at=now - timedelta(days=1)),
            Order(id=uid(), order_no="ORD-20260714003", contact_id=contact2_id,
                  product_name="蓝牙降噪耳机 Pro", quantity=1, total_amount=299.00,
                  status="paid", payment_status="paid",
                  shipping_address={"province": "上海市", "city": "上海市", "district": "浦东新区", "detail": "yyy路200号"},
                  logistics_no=None, logistics_status=None),
            Order(id=uid(), order_no="ORD-20260714004", contact_id=contact3_id,
                  product_name="经典款纯棉T恤", quantity=3, total_amount=297.00,
                  status="paid", payment_status="paid",
                  shipping_address={"province": "广州市", "city": "广州市", "district": "天河区", "detail": "zzz路300号"},
                  logistics_no=None, logistics_status=None, risk_flag=True),
        ]
        db.add_all(orders)
        print(f"  ✓ Created {len(orders)} orders")

        # ========== Knowledge Chunks ==========
        # 这些 chunk 没有 embedding（模拟数据），实际使用时通过 RAG pipeline 向量化
        chunks = [
            KnowledgeChunk(id=uid(), product_id=prod1_id, source_type="product_desc", title="T恤材质说明",
                           content="经典款纯棉T恤采用100%新疆长绒棉，经过预缩处理，不易变形。面料克重180g/m²，透气性极佳，适合春夏穿着。",
                           content_hash="a1b2c3d4e1", chunk_index=0, chunk_metadata={"source": "产品手册"}),
            KnowledgeChunk(id=uid(), product_id=prod1_id, source_type="size_chart", title="T恤尺码对照表",
                           content="S码：身高160-170cm，体重50-60kg；M码：身高165-175cm，体重55-70kg；L码：身高170-180cm，体重65-80kg；XL码：身高175-185cm，体重75-90kg；XXL码：身高180-195cm，体重85-105kg。",
                           content_hash="a1b2c3d4e2", chunk_index=1, chunk_metadata={"source": "尺码表"}),
            KnowledgeChunk(id=uid(), product_id=prod1_id, source_type="faq", title="T恤如何清洗",
                           content="建议30°C以下温水手洗或机洗，不可漂白，悬挂晾干。深色衣物首次洗涤可能会有轻微浮色，建议与浅色衣物分开洗涤。",
                           content_hash="a1b2c3d4e3", chunk_index=2, chunk_metadata={"source": "FAQ"}),
            KnowledgeChunk(id=uid(), product_id=prod2_id, source_type="product_desc", title="跑鞋技术参数",
                           content="Air Boost运动跑鞋采用Flyknit编织鞋面+全掌ZoomX泡棉中底，单只重量仅230g（42码）。橡胶外底耐磨防滑，适合公路和跑步机使用。",
                           content_hash="a1b2c3d4e4", chunk_index=0, chunk_metadata={"source": "产品手册"}),
            KnowledgeChunk(id=uid(), product_id=prod3_id, source_type="faq", title="耳机保修政策",
                           content="本产品享受1年官方质保服务。7天内出现质量问题可免费退换货，15天内可免费换货。人为损坏不在质保范围内。如需售后请联系客服并提供订单号。",
                           content_hash="a1b2c3d4e5", chunk_index=0, chunk_metadata={"source": "售后政策"}),
            KnowledgeChunk(id=uid(), source_type="policy", title="退换货政策",
                           content="自签收之日起7天内，商品未使用、包装完好可申请无理由退换货。已发货订单退款将在收到退回商品后1-3个工作日到账。未发货订单可随时取消并全额退款。",
                           content_hash="a1b2c3d4e6", chunk_index=0, chunk_metadata={"source": "售后政策"}),
            KnowledgeChunk(id=uid(), source_type="faq", title="发货时间",
                           content="正常情况下，订单支付成功后24小时内发货。大促期间可能延迟至48小时。默认发中通/圆通快递，可联系客服补差价发顺丰。",
                           content_hash="a1b2c3d4e7", chunk_index=0, chunk_metadata={"source": "FAQ"}),
        ]
        db.add_all(chunks)
        print(f"  ✓ Created {len(chunks)} knowledge chunks")

        await db.commit()
        print("\n✅ Seed data created successfully!")
        print(f"   Admin login: admin@smartcs.com / admin123")
        print(f"   Agent login: agent1@smartcs.com / agent123")


if __name__ == "__main__":
    asyncio.run(seed())
