from datetime import datetime

from sqlalchemy import inspect

from app.extension import db


# MEMBER
class Member(db.Model):
    __tablename__ = "member"

    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(db.String, unique=True, nullable=False)  # Logto sub
    timezone = db.Column(db.String(32), server_default="UTC")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email = db.Column(
        db.String(64), nullable=True
    )  #!!! не забыть переключить на False !!!
    last_active_role = db.Column(db.String(20), nullable=True)

    consents = db.relationship("MemberConsent", back_populates="member", cascade="all, delete-orphan")
    roles = db.relationship("MemberRole", back_populates="member", cascade="all, delete-orphan")
    specialist = db.relationship("Specialist", uselist=False, back_populates="member", cascade="all, delete-orphan")
    client = db.relationship("Client", uselist=False, back_populates="member", cascade="all, delete-orphan")
    verified_by = db.Column(db.Integer, db.ForeignKey("member.id", ondelete="SET NULL"))
    documents_verified = db.relationship("SpecialistDocuments", foreign_keys="SpecialistDocuments.verified_by")


# ROLES
class Role(db.Model):
    __tablename__ = "role"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True)
    label = db.Column(db.String(32))


def seed_role():

    inspector = inspect(db.engine)
    if "role" not in inspector.get_table_names():
        return  # таблицы ещё нет — выходим

    # Создадим дефолтные роли
    roles_data = [
        {"code": "client", "label": "Клиент"},
        {"code": "specialist", "label": "Специалист"},
        {"code": "moderator", "label": "Модератор"},
        {"code": "admin", "label": "Администратор"},
        {"code": "owner", "label": "Владелец"},
    ]

    for role_info in roles_data:
        role = Role.query.filter_by(code=role_info["code"]).first()
        if not role:
            new_role = Role(code=role_info["code"], label=role_info["label"])
            db.session.add(new_role)
    db.session.commit()


class MemberRole(db.Model):
    __tablename__ = "member_role"

    member_id = db.Column(db.Integer, db.ForeignKey("member.id", ondelete="CASCADE"), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)

    is_active = db.Column(db.Boolean, default=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship("Member", back_populates="roles")
    role = db.relationship("Role")


# CLIENT / SPECIALIST
class Specialist(db.Model):
    __tablename__ = "specialist"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id", ondelete="CASCADE"), unique=True)

    photo_url = db.Column(db.String)
    first_name = db.Column(db.String(32))
    last_name = db.Column(db.String(32))
    specialization = db.Column(db.String(64))
    education = db.Column(db.String(255))
    bio = db.Column(db.Text)
    experience_years = db.Column(db.Integer)
    base_price = db.Column(db.Integer, nullable=True, server_default="1500")
    verification_status = db.Column(db.String(20), default="pending")
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reject_reason = db.Column(db.String, nullable=True)

    member = db.relationship("Member", back_populates="specialist")
    slots = db.relationship("Slot", back_populates="specialist", cascade="all, delete-orphan")
    documents = db.relationship("SpecialistDocuments", back_populates="specialist", cascade="all, delete-orphan")


class SpecialistDocuments(db.Model):
    __tablename__ = "specialistdocument"

    id = db.Column(db.Integer, primary_key=True)

    verified_by = db.Column(db.Integer, db.ForeignKey("member.id"))
    specialist_id = db.Column(db.Integer, db.ForeignKey("specialist.id", ondelete="CASCADE"))

    document_title = db.Column(db.String(64), nullable=False)
    file_url = db.Column(db.String, nullable=False)

    is_active = db.Column(db.Boolean, default=True)
    uploaded_time = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    verification_status = db.Column(db.String(32), nullable=False)
    origin_name = db.Column(db.String(255))
    reject_reason = db.Column(db.String, nullable=True)

    # связи
    specialist = db.relationship("Specialist", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.document_title}>"


class Review(db.Model):
    __tablename__ = "review"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id", ondelete="CASCADE"), unique=True, nullable=False, 
    )
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), nullable=False)
    specialist_id = db.Column(
        db.Integer, db.ForeignKey("specialist.id", ondelete="CASCADE"), nullable=False
    )
    rating = db.Column(db.Integer, nullable=False)  # 1–5
    comment = db.Column(db.Text, nullable=True)
    is_approved = db.Column(db.Boolean, default=False)  # после модерации
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # связи
    appointment = db.relationship(
        "Appointment", backref=db.backref("review", uselist=False)
    )
    client = db.relationship("Client", backref="reviews")
    specialist = db.relationship("Specialist", backref="reviews")


class Client(db.Model):
    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), unique=True)

    avatar_url = db.Column(db.String)
    display_name = db.Column(db.String(64))
    bio = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship("Member", back_populates="client")
    appointments = db.relationship("Appointment", back_populates="client", cascade="all, delete-orphan")


# TAGS (ISSUE / METHOD)
class Issue(db.Model):
    __tablename__ = "issue"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True)
    label = db.Column(db.String(64))


class SpecialistIssue(db.Model):
    __tablename__ = "specialist_issue"

    specialist_id = db.Column(
        db.Integer, db.ForeignKey("specialist.id", ondelete="CASCADE"), primary_key=True
    )
    issue_id = db.Column(db.Integer, db.ForeignKey("issue.id", ondelete="CASCADE"), primary_key=True)


class Method(db.Model):
    __tablename__ = "method"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True)
    label = db.Column(db.String(64))


class SpecialistMethod(db.Model):
    __tablename__ = "specialist_method"

    specialist_id = db.Column(
        db.Integer, db.ForeignKey("specialist.id", ondelete="CASCADE"), primary_key=True
    )
    method_id = db.Column(db.Integer, db.ForeignKey("method.id", ondelete="CASCADE"), primary_key=True)


# SLOT (Cal.com)
class Slot(db.Model):
    __tablename__ = "slot"

    id = db.Column(db.Integer, primary_key=True)
    specialist_id = db.Column(
        db.Integer, db.ForeignKey("specialist.id", ondelete="CASCADE")
    )

    price = db.Column(db.Float, nullable=False, server_default="1500")

    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)

    external_id = db.Column(db.String)  # Cal.com ID
    provider = db.Column(db.String, default="cal.com")

    specialist = db.relationship("Specialist", back_populates="slots")
    appointments = db.relationship("Appointment", back_populates="slot", cascade="all, delete-orphan")


# APPOINTMENT
class AppointmentStatus(db.Model):
    __tablename__ = "appointment_status"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True)
    label = db.Column(db.String(32))


class Appointment(db.Model):
    __tablename__ = "appointment"

    id = db.Column(db.Integer, primary_key=True)

    slot_id = db.Column(db.Integer, db.ForeignKey("slot.id", ondelete="CASCADE"))
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"))
    status_id = db.Column(db.Integer, db.ForeignKey("appointment_status.id"))

    external_booking_id = db.Column(db.String)  # Cal.com booking ID
    booking_provider = db.Column(db.String, default="cal.com")

    price = db.Column(db.Float, nullable=False, server_default="1500")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    slot = db.relationship("Slot", back_populates="appointments")
    client = db.relationship("Client", back_populates="appointments")
    status = db.relationship("AppointmentStatus")

    payment = db.relationship("Payment", uselist=False, back_populates="appointment", cascade="all, delete-orphan")


# PAYMENT (YooKassa)
class Payment(db.Model):
    __tablename__ = "payment"

    id = db.Column(db.Integer, primary_key=True)

    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"))

    provider = db.Column(db.String(32))  # yookassa
    provider_payment_id = db.Column(db.String, unique=True)

    amount = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(8))

    status = db.Column(db.String(32))  # pending / succeeded / canceled

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)

    appointment = db.relationship("Appointment", back_populates="payment")


# CONSENTS


class ConsentType(db.Model):
    __tablename__ = "consent_type"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True)
    label = db.Column(db.String(64))


class Consent(db.Model):
    __tablename__ = "consent"

    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey("consent_type.id", ondelete="CASCADE"))

    version = db.Column(db.String(16))
    content_url = db.Column(db.String)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MemberConsent(db.Model):
    __tablename__ = "member_consent"

    member_id = db.Column(db.Integer, db.ForeignKey("member.id", ondelete="CASCADE"), primary_key=True)
    consent_id = db.Column(db.Integer, db.ForeignKey("consent.id", ondelete="CASCADE"), primary_key=True)

    accepted_at = db.Column(db.DateTime, default=datetime.utcnow)
    member = db.relationship("Member", back_populates="consents")
