"""
FairSplit seed script.

Populates two realistic expense groups with members, expenses (all three split
types represented), and settlements. Every seeded member lands on a populated
dashboard — no blank screens.

Design notes:
- No bcrypt: FairSplit uses display-name-only anonymous sessions (no passwords).
  There are no user accounts, no email addresses, and no login credentials.
  Members are identified by the JWT issued at join time.
- Idempotent: checks for existing groups by name before inserting, so the
  script is safe to re-run without duplicating data.
- Direct asyncpg inserts (not ORM) for speed and to avoid triggering
  ORM-level validation that does not apply during seeding.
- UUIDs are generated in Python so they can be printed in the summary.

Usage:
    DATABASE_URL=postgresql+asyncpg://fairsplit:fairsplit_dev@localhost:5432/fairsplit \
    python seed.py

Or from inside Docker:
    docker compose exec backend python seed.py
"""

import asyncio
import uuid
from datetime import date, datetime, timezone

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://fairsplit:fairsplit_dev@localhost:5432/fairsplit",
)


async def seed() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            await _seed_all(session)

    await engine.dispose()


async def _seed_all(session: AsyncSession) -> None:
    # ------------------------------------------------------------------
    # Group 1: Nashville Trip (active)
    # ------------------------------------------------------------------
    # Check idempotency: if this group already exists, skip it.
    existing_nashville = await session.execute(
        sa.text("SELECT id FROM groups WHERE name = 'Nashville Trip 2026' LIMIT 1")
    )
    if existing_nashville.fetchone() is not None:
        print("Seed data already present — skipping (idempotent run).")
        return

    # UUIDs for group 1
    g1_id = uuid.uuid4()
    g1_invite = uuid.uuid4()
    m1_maya = uuid.uuid4()    # admin
    m1_daniel = uuid.uuid4()  # member
    m1_priya = uuid.uuid4()   # member
    m1_jake = uuid.uuid4()    # member
    m1_rachel = uuid.uuid4()  # member

    # UUIDs for group 2: Roommates 2025 (archived)
    g2_id = uuid.uuid4()
    g2_invite = uuid.uuid4()
    m2_alex = uuid.uuid4()    # admin
    m2_sam = uuid.uuid4()     # member
    m2_jordan = uuid.uuid4()  # member

    # ----------------------------------------------------------------
    # Insert groups
    # ----------------------------------------------------------------
    await session.execute(sa.text("""
        INSERT INTO groups (id, name, description, invite_token, status, default_currency)
        VALUES
        (:id, :name, :description, :invite_token, :status, :currency)
    """), [
        {
            "id": g1_id,
            "name": "Nashville Trip 2026",
            "description": "June 2026 — 5 friends, 4 days, 1 Airbnb",
            "invite_token": g1_invite,
            "status": "active",
            "currency": "USD",
        },
        {
            "id": g2_id,
            "name": "Roommates 2025",
            "description": "Shared apartment expenses — 3 tenants, full year",
            "invite_token": g2_invite,
            "status": "archived",
            "currency": "USD",
        },
    ])

    # ----------------------------------------------------------------
    # Insert members
    # ----------------------------------------------------------------
    now = datetime.now(timezone.utc)

    await session.execute(sa.text("""
        INSERT INTO members (id, group_id, display_name, is_admin, joined_at)
        VALUES
        (:id, :group_id, :display_name, :is_admin, :joined_at)
    """), [
        # Group 1 — Nashville Trip
        {"id": m1_maya,   "group_id": g1_id, "display_name": "Maya",   "is_admin": True,  "joined_at": now},
        {"id": m1_daniel, "group_id": g1_id, "display_name": "Daniel", "is_admin": False, "joined_at": now},
        {"id": m1_priya,  "group_id": g1_id, "display_name": "Priya",  "is_admin": False, "joined_at": now},
        {"id": m1_jake,   "group_id": g1_id, "display_name": "Jake",   "is_admin": False, "joined_at": now},
        {"id": m1_rachel, "group_id": g1_id, "display_name": "Rachel", "is_admin": False, "joined_at": now},
        # Group 2 — Roommates
        {"id": m2_alex,   "group_id": g2_id, "display_name": "Alex",   "is_admin": True,  "joined_at": now},
        {"id": m2_sam,    "group_id": g2_id, "display_name": "Sam",    "is_admin": False, "joined_at": now},
        {"id": m2_jordan, "group_id": g2_id, "display_name": "Jordan", "is_admin": False, "joined_at": now},
    ])

    # ----------------------------------------------------------------
    # Insert expenses — Group 1 (Nashville Trip)
    # All amounts as integer cents (e.g., $840.00 = 84000)
    # ----------------------------------------------------------------

    # Expense 1: Airbnb deposit — equal split among all 5
    e1_airbnb = uuid.uuid4()
    # Expense 2: Groceries Day 1 — custom amount split
    e2_groceries = uuid.uuid4()
    # Expense 3: Dinner at The Row Kitchen — equal split
    e3_dinner = uuid.uuid4()
    # Expense 4: Pedal Tavern — custom percentage split
    e4_pedal = uuid.uuid4()
    # Expense 5: Gas for road trip — equal split
    e5_gas = uuid.uuid4()
    # Expense 6: Broadway show tickets — equal split (only 3 people went)
    e6_broadway = uuid.uuid4()
    # Expense 7: Late-night pizza — custom amount split
    e7_pizza = uuid.uuid4()
    # Expense 8: Uber rides — custom percentage split
    e8_uber = uuid.uuid4()
    # Expense 9: Souvenirs — Daniel paid for 2 people
    e9_souvenirs = uuid.uuid4()
    # Expense 10: Brunch on day 3 — equal split all 5
    e10_brunch = uuid.uuid4()

    await session.execute(sa.text("""
        INSERT INTO expenses
            (id, group_id, payer_member_id, logged_by_member_id, description,
             amount_cents, currency, split_type, expense_date)
        VALUES
        (:id, :group_id, :payer, :logger, :description, :amount, :currency, :split_type, :expense_date)
    """), [
        {
            "id": e1_airbnb, "group_id": g1_id,
            "payer": m1_maya, "logger": m1_maya,
            "description": "Airbnb — 4 nights in East Nashville",
            "amount": 84000, "currency": "USD", "split_type": "equal",
            "expense_date": date(2026, 6, 10),
        },
        {
            "id": e2_groceries, "group_id": g1_id,
            "payer": m1_priya, "logger": m1_priya,
            "description": "Whole Foods haul — snacks and drinks for the house",
            "amount": 8740, "currency": "USD", "split_type": "custom_amount",
            "expense_date": date(2026, 6, 10),
        },
        {
            "id": e3_dinner, "group_id": g1_id,
            "payer": m1_jake, "logger": m1_maya,
            "description": "The Row Kitchen & Pub — Tuesday dinner",
            "amount": 31200, "currency": "USD", "split_type": "equal",
            "expense_date": date(2026, 6, 11),
        },
        {
            "id": e4_pedal, "group_id": g1_id,
            "payer": m1_maya, "logger": m1_maya,
            "description": "Nashville Pedal Tavern — 2-hour tour",
            "amount": 22500, "currency": "USD", "split_type": "custom_percentage",
            "expense_date": date(2026, 6, 11),
        },
        {
            "id": e5_gas, "group_id": g1_id,
            "payer": m1_daniel, "logger": m1_daniel,
            "description": "Gas for drive from Atlanta to Nashville",
            "amount": 6200, "currency": "USD", "split_type": "equal",
            "expense_date": date(2026, 6, 10),
        },
        {
            "id": e6_broadway, "group_id": g1_id,
            "payer": m1_rachel, "logger": m1_rachel,
            "description": "Ryman Auditorium tickets — Maya, Rachel, Priya",
            "amount": 33000, "currency": "USD", "split_type": "equal",
            "expense_date": date(2026, 6, 12),
        },
        {
            "id": e7_pizza, "group_id": g1_id,
            "payer": m1_jake, "logger": m1_jake,
            "description": "Five Points Pizza — midnight snack",
            "amount": 5800, "currency": "USD", "split_type": "custom_amount",
            "expense_date": date(2026, 6, 12),
        },
        {
            "id": e8_uber, "group_id": g1_id,
            "payer": m1_priya, "logger": m1_priya,
            "description": "Uber rides (Broadway to Airbnb x3)",
            "amount": 4800, "currency": "USD", "split_type": "custom_percentage",
            "expense_date": date(2026, 6, 13),
        },
        {
            "id": e9_souvenirs, "group_id": g1_id,
            "payer": m1_daniel, "logger": m1_daniel,
            "description": "Nashville hot chicken sauce sets for family",
            "amount": 3400, "currency": "USD", "split_type": "custom_amount",
            "expense_date": date(2026, 6, 13),
        },
        {
            "id": e10_brunch, "group_id": g1_id,
            "payer": m1_rachel, "logger": m1_rachel,
            "description": "Milk & Honey brunch — all 5",
            "amount": 19800, "currency": "USD", "split_type": "equal",
            "expense_date": date(2026, 6, 13),
        },
    ])

    # ----------------------------------------------------------------
    # Insert expense_splits — Group 1
    # ----------------------------------------------------------------

    # e1: Airbnb — equal split, 84000 / 5 = 16800 each
    airbnb_per_person = 84000 // 5  # 16800
    await session.execute(sa.text("""
        INSERT INTO expense_splits (id, expense_id, member_id, amount_cents, percentage)
        VALUES (:id, :expense_id, :member_id, :amount_cents, :percentage)
    """), [
        {"id": uuid.uuid4(), "expense_id": e1_airbnb, "member_id": m1_maya,   "amount_cents": airbnb_per_person, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e1_airbnb, "member_id": m1_daniel, "amount_cents": airbnb_per_person, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e1_airbnb, "member_id": m1_priya,  "amount_cents": airbnb_per_person, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e1_airbnb, "member_id": m1_jake,   "amount_cents": airbnb_per_person, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e1_airbnb, "member_id": m1_rachel, "amount_cents": airbnb_per_person, "percentage": None},
    ])

    # e2: Groceries — custom amount split (8740 total)
    # Maya: 2000, Daniel: 1500, Priya: 2000 (payer), Jake: 1740, Rachel: 1500
    await session.execute(sa.text("""
        INSERT INTO expense_splits (id, expense_id, member_id, amount_cents, percentage)
        VALUES (:id, :expense_id, :member_id, :amount_cents, :percentage)
    """), [
        {"id": uuid.uuid4(), "expense_id": e2_groceries, "member_id": m1_maya,   "amount_cents": 2000, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e2_groceries, "member_id": m1_daniel, "amount_cents": 1500, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e2_groceries, "member_id": m1_priya,  "amount_cents": 2000, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e2_groceries, "member_id": m1_jake,   "amount_cents": 1740, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e2_groceries, "member_id": m1_rachel, "amount_cents": 1500, "percentage": None},
    ])

    # e3: Dinner — equal split, 31200 / 5 = 6240 each
    dinner_per = 31200 // 5  # 6240
    await session.execute(sa.text("""
        INSERT INTO expense_splits (id, expense_id, member_id, amount_cents, percentage)
        VALUES (:id, :expense_id, :member_id, :amount_cents, :percentage)
    """), [
        {"id": uuid.uuid4(), "expense_id": e3_dinner, "member_id": m1_maya,   "amount_cents": dinner_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e3_dinner, "member_id": m1_daniel, "amount_cents": dinner_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e3_dinner, "member_id": m1_priya,  "amount_cents": dinner_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e3_dinner, "member_id": m1_jake,   "amount_cents": dinner_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e3_dinner, "member_id": m1_rachel, "amount_cents": dinner_per, "percentage": None},
    ])

    # e4: Pedal Tavern — custom percentage (22500 total)
    # Maya 25%, Daniel 20%, Priya 20%, Jake 20%, Rachel 15%
    # Amounts: 5625, 4500, 4500, 4500, 3375 = 22500 (exact)
    await session.execute(sa.text("""
        INSERT INTO expense_splits (id, expense_id, member_id, amount_cents, percentage)
        VALUES (:id, :expense_id, :member_id, :amount_cents, :percentage)
    """), [
        {"id": uuid.uuid4(), "expense_id": e4_pedal, "member_id": m1_maya,   "amount_cents": 5625, "percentage": "25.000"},
        {"id": uuid.uuid4(), "expense_id": e4_pedal, "member_id": m1_daniel, "amount_cents": 4500, "percentage": "20.000"},
        {"id": uuid.uuid4(), "expense_id": e4_pedal, "member_id": m1_priya,  "amount_cents": 4500, "percentage": "20.000"},
        {"id": uuid.uuid4(), "expense_id": e4_pedal, "member_id": m1_jake,   "amount_cents": 4500, "percentage": "20.000"},
        {"id": uuid.uuid4(), "expense_id": e4_pedal, "member_id": m1_rachel, "amount_cents": 3375, "percentage": "15.000"},
    ])

    # e5: Gas — equal split, 6200 / 5 = 1240 each
    gas_per = 6200 // 5  # 1240
    await session.execute(sa.text("""
        INSERT INTO expense_splits (id, expense_id, member_id, amount_cents, percentage)
        VALUES (:id, :expense_id, :member_id, :amount_cents, :percentage)
    """), [
        {"id": uuid.uuid4(), "expense_id": e5_gas, "member_id": m1_maya,   "amount_cents": gas_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e5_gas, "member_id": m1_daniel, "amount_cents": gas_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e5_gas, "member_id": m1_priya,  "amount_cents": gas_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e5_gas, "member_id": m1_jake,   "amount_cents": gas_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e5_gas, "member_id": m1_rachel, "amount_cents": gas_per, "percentage": None},
    ])

    # e6: Broadway — equal split among Maya, Rachel, Priya only (3 people, 33000 / 3 = 11000)
    await session.execute(sa.text("""
        INSERT INTO expense_splits (id, expense_id, member_id, amount_cents, percentage)
        VALUES (:id, :expense_id, :member_id, :amount_cents, :percentage)
    """), [
        {"id": uuid.uuid4(), "expense_id": e6_broadway, "member_id": m1_maya,   "amount_cents": 11000, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e6_broadway, "member_id": m1_rachel, "amount_cents": 11000, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e6_broadway, "member_id": m1_priya,  "amount_cents": 11000, "percentage": None},
    ])

    # e7: Pizza — custom amount (5800 total), Jake (payer) + Maya + Daniel
    # Jake: 2200, Maya: 1800, Daniel: 1800 = 5800
    await session.execute(sa.text("""
        INSERT INTO expense_splits (id, expense_id, member_id, amount_cents, percentage)
        VALUES (:id, :expense_id, :member_id, :amount_cents, :percentage)
    """), [
        {"id": uuid.uuid4(), "expense_id": e7_pizza, "member_id": m1_jake,   "amount_cents": 2200, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e7_pizza, "member_id": m1_maya,   "amount_cents": 1800, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e7_pizza, "member_id": m1_daniel, "amount_cents": 1800, "percentage": None},
    ])

    # e8: Uber — custom percentage (4800 total), Priya + Jake + Rachel
    # Priya 40%, Jake 35%, Rachel 25%
    # Amounts: 1920, 1680, 1200 = 4800 (exact)
    await session.execute(sa.text("""
        INSERT INTO expense_splits (id, expense_id, member_id, amount_cents, percentage)
        VALUES (:id, :expense_id, :member_id, :amount_cents, :percentage)
    """), [
        {"id": uuid.uuid4(), "expense_id": e8_uber, "member_id": m1_priya,  "amount_cents": 1920, "percentage": "40.000"},
        {"id": uuid.uuid4(), "expense_id": e8_uber, "member_id": m1_jake,   "amount_cents": 1680, "percentage": "35.000"},
        {"id": uuid.uuid4(), "expense_id": e8_uber, "member_id": m1_rachel, "amount_cents": 1200, "percentage": "25.000"},
    ])

    # e9: Souvenirs — custom amount (3400), Daniel (payer) + Maya
    # Daniel: 1700, Maya: 1700 = 3400
    await session.execute(sa.text("""
        INSERT INTO expense_splits (id, expense_id, member_id, amount_cents, percentage)
        VALUES (:id, :expense_id, :member_id, :amount_cents, :percentage)
    """), [
        {"id": uuid.uuid4(), "expense_id": e9_souvenirs, "member_id": m1_daniel, "amount_cents": 1700, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e9_souvenirs, "member_id": m1_maya,   "amount_cents": 1700, "percentage": None},
    ])

    # e10: Brunch — equal split all 5, 19800 / 5 = 3960 each
    brunch_per = 19800 // 5  # 3960
    await session.execute(sa.text("""
        INSERT INTO expense_splits (id, expense_id, member_id, amount_cents, percentage)
        VALUES (:id, :expense_id, :member_id, :amount_cents, :percentage)
    """), [
        {"id": uuid.uuid4(), "expense_id": e10_brunch, "member_id": m1_maya,   "amount_cents": brunch_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e10_brunch, "member_id": m1_daniel, "amount_cents": brunch_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e10_brunch, "member_id": m1_priya,  "amount_cents": brunch_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e10_brunch, "member_id": m1_jake,   "amount_cents": brunch_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e10_brunch, "member_id": m1_rachel, "amount_cents": brunch_per, "percentage": None},
    ])

    # ----------------------------------------------------------------
    # Insert settlements — Group 1 (1 completed settlement)
    # Daniel paid Maya $42.00 to partially clear his Airbnb debt
    # ----------------------------------------------------------------
    await session.execute(sa.text("""
        INSERT INTO settlements (id, group_id, payer_member_id, payee_member_id, amount_cents, currency)
        VALUES (:id, :group_id, :payer, :payee, :amount_cents, :currency)
    """), [
        {
            "id": uuid.uuid4(),
            "group_id": g1_id,
            "payer": m1_daniel,
            "payee": m1_maya,
            "amount_cents": 4200,
            "currency": "USD",
        },
    ])

    # ----------------------------------------------------------------
    # Group 2: Roommates 2025 — 4 expenses (archived group)
    # ----------------------------------------------------------------
    e_rent = uuid.uuid4()
    e_wifi = uuid.uuid4()
    e_cleaning = uuid.uuid4()
    e_electricity = uuid.uuid4()

    await session.execute(sa.text("""
        INSERT INTO expenses
            (id, group_id, payer_member_id, logged_by_member_id, description,
             amount_cents, currency, split_type, expense_date)
        VALUES
        (:id, :group_id, :payer, :logger, :description, :amount, :currency, :split_type, :expense_date)
    """), [
        {
            "id": e_rent, "group_id": g2_id,
            "payer": m2_alex, "logger": m2_alex,
            "description": "July rent — 3 equal shares",
            "amount": 390000, "currency": "USD", "split_type": "equal",
            "expense_date": date(2025, 7, 1),
        },
        {
            "id": e_wifi, "group_id": g2_id,
            "payer": m2_sam, "logger": m2_sam,
            "description": "Comcast Xfinity — July internet",
            "amount": 8900, "currency": "USD", "split_type": "equal",
            "expense_date": date(2025, 7, 3),
        },
        {
            "id": e_cleaning, "group_id": g2_id,
            "payer": m2_jordan, "logger": m2_jordan,
            "description": "Professional apartment cleaning — end of tenancy",
            "amount": 25000, "currency": "USD", "split_type": "custom_percentage",
            "expense_date": date(2025, 12, 28),
        },
        {
            "id": e_electricity, "group_id": g2_id,
            "payer": m2_alex, "logger": m2_alex,
            "description": "ConEd electricity — December (higher due to heating)",
            "amount": 19200, "currency": "USD", "split_type": "custom_amount",
            "expense_date": date(2025, 12, 30),
        },
    ])

    # Splits — Group 2
    rent_per = 390000 // 3   # 130000
    wifi_per = 8900 // 3     # 2966 (with 2-cent remainder — assign to Alex alphabetically)
    wifi_remainder = 8900 - (wifi_per * 3)  # = 2

    await session.execute(sa.text("""
        INSERT INTO expense_splits (id, expense_id, member_id, amount_cents, percentage)
        VALUES (:id, :expense_id, :member_id, :amount_cents, :percentage)
    """), [
        # Rent — equal
        {"id": uuid.uuid4(), "expense_id": e_rent, "member_id": m2_alex,   "amount_cents": rent_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e_rent, "member_id": m2_sam,    "amount_cents": rent_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e_rent, "member_id": m2_jordan, "amount_cents": rent_per, "percentage": None},
        # WiFi — equal with remainder assigned to Alex (first alphabetically)
        {"id": uuid.uuid4(), "expense_id": e_wifi, "member_id": m2_alex,   "amount_cents": wifi_per + wifi_remainder, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e_wifi, "member_id": m2_sam,    "amount_cents": wifi_per, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e_wifi, "member_id": m2_jordan, "amount_cents": wifi_per, "percentage": None},
        # Cleaning — custom percentage (25000)
        # Alex 40%, Sam 35%, Jordan 25%
        # Amounts: 10000, 8750, 6250 = 25000 (exact)
        {"id": uuid.uuid4(), "expense_id": e_cleaning, "member_id": m2_alex,   "amount_cents": 10000, "percentage": "40.000"},
        {"id": uuid.uuid4(), "expense_id": e_cleaning, "member_id": m2_sam,    "amount_cents": 8750,  "percentage": "35.000"},
        {"id": uuid.uuid4(), "expense_id": e_cleaning, "member_id": m2_jordan, "amount_cents": 6250,  "percentage": "25.000"},
        # Electricity — custom amount (19200)
        # Alex (master bedroom): 8400, Sam: 5400, Jordan: 5400 = 19200
        {"id": uuid.uuid4(), "expense_id": e_electricity, "member_id": m2_alex,   "amount_cents": 8400, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e_electricity, "member_id": m2_sam,    "amount_cents": 5400, "percentage": None},
        {"id": uuid.uuid4(), "expense_id": e_electricity, "member_id": m2_jordan, "amount_cents": 5400, "percentage": None},
    ])

    # Settlements — Group 2 (fully settled — archived group)
    await session.execute(sa.text("""
        INSERT INTO settlements (id, group_id, payer_member_id, payee_member_id, amount_cents, currency)
        VALUES (:id, :group_id, :payer, :payee, :amount_cents, :currency)
    """), [
        {
            "id": uuid.uuid4(),
            "group_id": g2_id,
            "payer": m2_sam,
            "payee": m2_alex,
            "amount_cents": 13000,
            "currency": "USD",
        },
        {
            "id": uuid.uuid4(),
            "group_id": g2_id,
            "payer": m2_jordan,
            "payee": m2_alex,
            "amount_cents": 11750,
            "currency": "USD",
        },
    ])

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    print("\nSeed complete.")
    print()
    print("  Groups:")
    print(f"    Nashville Trip 2026   id={g1_id}  invite_token={g1_invite}  (active)")
    print(f"    Roommates 2025        id={g2_id}  invite_token={g2_invite}  (archived)")
    print()
    print("  Members (Nashville Trip 2026):")
    print(f"    Maya    id={m1_maya}   (admin)")
    print(f"    Daniel  id={m1_daniel} (member)")
    print(f"    Priya   id={m1_priya}  (member)")
    print(f"    Jake    id={m1_jake}   (member)")
    print(f"    Rachel  id={m1_rachel} (member)")
    print()
    print("  Members (Roommates 2025):")
    print(f"    Alex    id={m2_alex}   (admin)")
    print(f"    Sam     id={m2_sam}    (member)")
    print(f"    Jordan  id={m2_jordan} (member)")
    print()
    print("  Expenses seeded: 10 (Nashville Trip) + 4 (Roommates) = 14 total")
    print("  Settlements:     1 (Nashville Trip) + 2 (Roommates) = 3 total")
    print()
    print("  Dev links (join an existing group without creating a new one):")
    print(f"    Nashville Trip admin  — open http://localhost:3000/join/{g1_invite}")
    print(f"    Roommates admin       — open http://localhost:3000/join/{g2_invite}")
    print()
    print("  Note: FairSplit uses anonymous sessions (display name only).")
    print("  There are no email/password credentials to log in with.")
    print("  Use the join links above to create a new session as any member.")
    print()


asyncio.run(seed())
