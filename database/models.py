from sqlalchemy import String, Text, BigInteger, ForeignKey, Boolean, Integer, DateTime, Numeric, func, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from datetime import timezone, datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint('username', name='uq_users_username'),
        CheckConstraint('energy >= 0', name='ck_users_energy_nonneg'),
        CheckConstraint('ltv >= 0', name='ck_users_ltv_nonneg'),
        CheckConstraint('pay_cnt >= 0', name='ck_users_pay_cnt_nonneg'),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True
    )

    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    registration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    energy: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    subscription_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    ltv: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal('0.00')
    )

    pay_cnt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    
    purchases: Mapped[list["Purchase"]] = relationship(
        "Purchase", back_populates="user"
    )
    
    
class Product(Base):
    __tablename__ = 'product'
    __table_args__ = (
        CheckConstraint('cost >= 0', name='ck_product_cost_nonneg'),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        primary_key=True
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal('0.00')
    )

    # обратная связь на покупки
    purchases: Mapped[list["Purchase"]] = relationship(
        "Purchase",
        back_populates="product",
        cascade="all, delete-orphan"
    )


class Purchase(Base):
    __tablename__ = 'purchases'
    __table_args__ = (
        CheckConstraint('amount >= 0', name='ck_purchases_amount_nonneg'),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    product_name: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("product.name", ondelete="RESTRICT"),
        nullable=False
    )
    purchase_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    method: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal('0.00')
    )

    # связи
    user: Mapped["User"] = relationship(
        "User",
        back_populates="purchases"
    )
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="purchases"
    )