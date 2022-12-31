from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine


id: Optional[int] = Field(default=None, primary_key=True)
name: str = None
secret_name: str = None
age: Optional[int] = None
Hero = type("Hero", (SQLModel, {"table": True}), {
    "id": id,
    "name": name,
    "secret_name": secret_name,
    "age": age,
})


hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)


engine = create_engine("sqlite:///database.db")


SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    session.add(hero_1)
    session.add(hero_2)
    session.add(hero_3)
    session.commit()
