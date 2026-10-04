"""Wipe the public demo instance and reseed it with a small, presentable log.

Destructive: it truncates every table, so it refuses to run unless
``BLOOM_DEMO_RESET=yes`` is set. Point it at a database with the usual
``POSTGRES_*`` variables.

    BLOOM_DEMO_RESET=yes uv run python scripts/reset_demo.py
"""

import os
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from bloom.core.config import get_settings
from bloom.db import models
from bloom.db.base import Base
from bloom.db.session import SessionLocal
from bloom.services import auth_service, users_service

DEMO_EMAIL = os.getenv("BLOOM_DEMO_EMAIL", "barista@barista.com")
DEMO_USERNAME = os.getenv("BLOOM_DEMO_USERNAME", "barista")
DEMO_PASSWORD = os.getenv("BLOOM_DEMO_PASSWORD", "baristademo")

ROASTERS = [
    ("Nomad Coffee", "Spain", "Barcelona"),
    ("Right Side Coffee", "Spain", "Barcelona"),
    ("Hola Coffee", "Spain", "Madrid"),
    ("La Cabra", "Denmark", "Aarhus"),
]

METHODS = [
    ("V60", "filter", Decimal("16.67")),
    ("Chemex", "filter", Decimal("16.00")),
    ("AeroPress", "immersion", Decimal("14.00")),
    ("French Press", "immersion", Decimal("15.00")),
    ("Espresso", "espresso", Decimal("2.00")),
]

EQUIPMENT = [
    ("grinder", "Niche Zero", "Niche"),
    ("grinder", "Comandante C40", "Comandante"),
    ("espresso_machine", "Lelit Bianca", "Lelit"),
    ("kettle", "Fellow Stagg EKG", "Fellow"),
]

# Spread across roast types and origins so the list filters have something to bite on.
BEANS = [
    ("Kiamabara AA", 0, "Kenya", "Nyeri", "washed", "light", "filter", 5, "Blackcurrant, tomato, cane sugar"),
    ("Guji Shakiso", 1, "Ethiopia", "Guji", "natural", "light", "filter", 4, "Blueberry, jasmine, peach"),
    ("El Paraíso Lychee", 2, "Colombia", "Cauca", "anaerobic", "medium", "omni", 5, "Lychee, rose, candy"),
    ("Fazenda Rainha", 3, "Brazil", "Mogiana", "natural", "medium_dark", "espresso", 3, "Hazelnut, milk chocolate"),
    ("Las Lajas Perla Negra", 0, "Costa Rica", "Central Valley", "honey", "medium", "omni", 4, "Red apple, brown sugar"),
    ("Finca Tamana", 2, "Colombia", "Huila", "washed", "medium", "espresso", 4, "Caramel, orange, almond"),
]

# (bean index, method index, name, dose, yield, water, grind, temp, seconds, notes)
RECIPES = [
    (0, 0, "Bright washed V60", "15.0", None, "250.0", "22", "94.0", 165, "Rinse the filter, 45 s bloom, pour in 3 stages."),
    (1, 0, "Floral natural, slightly cooler", "15.0", None, "250.0", "21", "93.0", 172, "Cooler water keeps the jasmine up front."),
    (2, 4, "Sweet 1:2 espresso", "18.0", "38.0", None, "2.4", "93.0", 28, "Ease off the pressure after pre-infusion."),
    (3, 4, "Milk-drink espresso", "18.5", "37.0", None, "2.2", "92.0", 26, "Lower temperature to tame bitterness in milk."),
    (4, 2, "Inverted AeroPress", "14.0", None, "200.0", "18", "88.0", 120, None),
]

# Recipe indexes the demo user has favorited.
FAVORITE_RECIPES = (0, 2)

# brew index -> recipe index it was made from; the remaining brews have no recipe.
BREW_RECIPES = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}

# (bean index, method index, dose, yield, water, grind, temp, seconds, tds, days ago)
BREWS = [
    (0, 0, "15.0", None, "250.0", "22", "94.0", 165, "1.38", 0),
    (1, 0, "15.0", None, "250.0", "21", "93.0", 172, "1.41", 1),
    (2, 4, "18.0", "38.0", None, "2.4", "93.0", 28, "9.20", 1),
    (3, 4, "18.5", "37.0", None, "2.2", "92.0", 26, "10.10", 2),
    (4, 2, "14.0", None, "200.0", "18", "88.0", 120, "1.32", 3),
    (5, 4, "18.0", "36.0", None, "2.3", "93.5", 30, "9.80", 4),
    (0, 1, "30.0", None, "500.0", "24", "94.0", 240, None, 6),
    (4, 3, "30.0", None, "450.0", "28", "95.0", 480, None, 8),
]

# Scores are 1-5. Deliberately partial: the last brews stay untasted, so the
# "Not tasted" filter has something to show.
TASTINGS = [
    (0, 5, 5, 4, 3, 2, 4, 5, ["blackcurrant", "tomato"], "Juicy and bright, would grind finer."),
    (1, 5, 4, 4, 3, 1, 4, 5, ["blueberry", "jasmine"], "Best cup of the week."),
    (2, 4, 4, 5, 4, 2, 4, 4, ["lychee", "rose"], None),
    (3, 3, 2, 4, 5, 3, 3, 3, ["hazelnut", "chocolate"], "Heavy body, a bit flat."),
    (4, 4, 3, 4, 4, 2, 4, 4, ["apple", "brown sugar"], None),
]


def truncate_everything(db: Session) -> None:
    """Empty every table the ORM knows about, resetting identity counters.

    Alembic's version table is not part of the metadata, so migration state
    survives and the app does not re-run migrations on its next boot.
    """
    tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    db.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
    db.commit()


def seed(db: Session) -> None:
    # The admin is normally created on boot; nothing restarts the demo after a wipe.
    if auth_service.bootstrap_admin(db) is None:
        print("No BLOOM_ADMIN_EMAIL/PASSWORD set: the demo is left without an admin account.")

    demo = users_service.create_user(db, email=DEMO_EMAIL, username=DEMO_USERNAME, password=DEMO_PASSWORD, role="user")

    roasters = [models.Roaster(name=name, country=country, city=city) for name, country, city in ROASTERS]
    methods = [models.BrewMethod(name=name, category=category, default_ratio=ratio) for name, category, ratio in METHODS]
    equipment = [models.Equipment(type=type_, name=name, brand=brand) for type_, name, brand in EQUIPMENT]
    db.add_all(roasters + methods + equipment)
    db.flush()

    beans = []
    for name, roaster, country, region, process, roast_level, roast_type, rating, notes_label in BEANS:
        beans.append(
            models.Bean(
                user_id=demo.id,
                name=name,
                roaster_id=roasters[roaster].id,
                origin_country=country,
                region=region,
                process=process,
                roast_level=roast_level,
                roast_type=roast_type,
                rating=rating,
                tasting_notes_label=notes_label,
            )
        )
    db.add_all(beans)
    db.flush()

    today = date.today()
    lots = [
        models.BeanLot(
            bean_id=bean.id,
            user_id=demo.id,
            roast_date=today - timedelta(days=10 + index * 3),
            purchase_date=today - timedelta(days=7 + index * 3),
            weight_grams=250,
            price=Decimal("14.50"),
        )
        for index, bean in enumerate(beans[:4])
    ]
    db.add_all(lots)
    db.flush()

    recipes = [
        models.Recipe(
            user_id=demo.id,
            bean_id=beans[bean].id,
            method_id=methods[method].id,
            grinder_id=equipment[0].id if methods[method].category == "espresso" else equipment[1].id,
            name=name,
            dose_grams=Decimal(dose),
            yield_grams=Decimal(yield_g) if yield_g else None,
            water_grams=Decimal(water) if water else None,
            grind_setting=grind,
            water_temp_celsius=Decimal(temp),
            brew_time_seconds=seconds,
            notes=notes,
        )
        for bean, method, name, dose, yield_g, water, grind, temp, seconds, notes in RECIPES
    ]
    db.add_all(recipes)
    db.flush()
    db.add_all(models.RecipeFavorite(user_id=demo.id, recipe_id=recipes[index].id) for index in FAVORITE_RECIPES)

    now = datetime.now(UTC)
    brews = []
    for index, (bean, method, dose, yield_g, water, grind, temp, seconds, tds, days_ago) in enumerate(BREWS):
        brews.append(
            models.Brew(
                user_id=demo.id,
                bean_id=beans[bean].id,
                method_id=methods[method].id,
                grinder_id=equipment[0].id if methods[method].category == "espresso" else equipment[1].id,
                recipe_id=recipes[BREW_RECIPES[index]].id if index in BREW_RECIPES else None,
                brewed_at=now - timedelta(days=days_ago, hours=days_ago),
                dose_grams=Decimal(dose),
                yield_grams=Decimal(yield_g) if yield_g else None,
                water_grams=Decimal(water) if water else None,
                grind_setting=grind,
                water_temp_celsius=Decimal(temp),
                brew_time_seconds=seconds,
                tds_percent=Decimal(tds) if tds else None,
            )
        )
    db.add_all(brews)
    db.flush()

    db.add_all(
        models.Tasting(
            brew_id=brews[brew].id,
            user_id=demo.id,
            aroma=aroma,
            acidity=acidity,
            sweetness=sweetness,
            body=body,
            bitterness=bitterness,
            aftertaste=aftertaste,
            overall=overall,
            descriptors=descriptors,
            notes=notes,
        )
        for brew, aroma, acidity, sweetness, body, bitterness, aftertaste, overall, descriptors, notes in TASTINGS
    )
    db.commit()

    print(
        f"Seeded {len(beans)} beans, {len(lots)} lots, {len(recipes)} recipes, {len(brews)} brews "
        f"and {len(TASTINGS)} tastings for {DEMO_USERNAME}."
    )


def main() -> None:
    if os.getenv("BLOOM_DEMO_RESET") != "yes":
        sys.exit("Refusing to run: this wipes every table. Set BLOOM_DEMO_RESET=yes if that is what you want.")

    settings = get_settings()
    print(f"Resetting {settings.POSTGRES_DB} on {settings.POSTGRES_SERVER}...")

    db = SessionLocal()
    try:
        truncate_everything(db)
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
