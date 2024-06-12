import datetime
from typing import Optional

import sqlalchemy
import sqlalchemy.orm
from passlib.hash import bcrypt
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

engine = sqlalchemy.create_engine("sqlite:///data/expenses.db", echo=False)


class Base(sqlalchemy.orm.DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    password: Mapped[str]


class Bill(Base):
    __tablename__ = "bills"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    datetime: Mapped[datetime.datetime]
    value: Mapped[float]


class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str]
    value: Mapped[float]
    quantity: Mapped[int] = mapped_column(default=1)
    price_per_item: Mapped[Optional[float]]
    weight: Mapped[Optional[float]]
    price_per_kg: Mapped[Optional[float]]
    tags: Mapped[Optional[str]]
    datetime: Mapped[datetime.datetime]

    def __repr__(self):
        return (
            "Expense("
            f"id={self.id}, "
            f"bill_id={self.bill_id}, "
            f"name={self.name},"
            f"quantity={self.quantity},"
            f"value={self.value}"
            ")"
        )


def create_database():
    Base.metadata.create_all(engine)


def clean():
    Base.metadata.drop_all(engine)


def orm_object_to_dict(expense: Expense):
    d = expense.__dict__
    d.pop("_sa_instance_state")
    return d


def register(user_name: str, password: str):
    hash_ = bcrypt.hash(password)
    with sqlalchemy.orm.Session(engine) as session:
        user = User(name=user_name, password=hash_)
        session.add(user)
        session.commit()


def find_user(user_name: str, password: str = None):
    with sqlalchemy.orm.Session(engine) as session:
        results = session.query(User).filter(User.name == user_name).all()
        if not results:
            return None
        assert len(results) == 1
        user = results[0]
        if password is not None and not bcrypt.verify(password, user.password):
            return None
        return user


def jsonify_bill(bill: Bill = None, bill_id: int = None):
    with sqlalchemy.orm.Session(engine) as session:
        if bill_id is None:
            assert bill is not None
        else:
            query = session.query(Bill).filter(Bill.id == bill_id)
            results = query.all()
            assert len(results) == 1
            bill = results[0]
    with sqlalchemy.orm.Session(engine) as session:
        query = session.query(Expense).filter(Expense.bill_id == bill.id)
        expenses = [orm_object_to_dict(e) for e in query.all()]
        return dict(**orm_object_to_dict(bill), expenses=expenses)


def get_bills(user: User):
    with sqlalchemy.orm.Session(engine) as session:
        query = (
            session.query(Bill)
            .filter(Bill.user_id == user.id)
            .order_by(Bill.datetime.desc())
            .limit(10)
        )
        bills = query.all()

    data = []
    for bill in bills:
        data.append(jsonify_bill(bill))
    return data


def retrieve_sum_expenses(
    user: User,
    start: datetime.date,
    stop: datetime.date,
    dt: datetime.timedelta,
):
    assert stop > start
    assert (start + 1000 * dt) > stop
    data = []
    x = start
    while x <= stop:
        with sqlalchemy.orm.Session(engine) as session:
            value = (
                session.query(sqlalchemy.func.sum(Bill.value))
                .filter(Bill.datetime >= x)
                .filter(Bill.datetime < x + dt)
                .filter(Bill.user_id == user.id)
                .order_by(Bill.datetime)
                .scalar()
            )
            value = 0 if value is None else value
            data.append(dict(x=x, y=value))
            session.close()
        x += dt
    return data
