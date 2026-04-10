from app.extension import db
from datetime import datetime
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


# MEMBER
class Member(db.Model):
    __tablename__ = 'member'

    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(db.String, unique=True, nullable=False)  # Logto sub
    timezone = db.Column(db.String(32))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    roles = db.relationship('MemberRole', back_populates='member')
    specialist = db.relationship('Specialist', uselist=False, back_populates='member')
    client = db.relationship('Client', uselist=False, back_populates='member')


# ROLES
class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True)
    label = db.Column(db.String(32))


class MemberRole(db.Model):
    __tablename__ = 'member_role'

    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), primary_key=True)

    is_active = db.Column(db.Boolean, default=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', back_populates='roles')
    role = db.relationship('Role')



# CLIENT / SPECIALIST
class Specialist(db.Model):
    __tablename__ = 'specialist'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), unique=True)

    photo_url = db.Column(db.String)
    first_name = db.Column(db.String(32))
    last_name = db.Column(db.String(32))
    bio = db.Column(db.Text)
    experience_years = db.Column(db.Integer)
    base_price = db.Column(db.Integer)

    is_visible = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', back_populates='specialist')
    slots = db.relationship('Slot', back_populates='specialist')


class Client(db.Model):
    __tablename__ = 'client'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), unique=True)

    avatar_url = db.Column(db.String)
    display_name = db.Column(db.String(64))
    bio = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', back_populates='client')
    appointments = db.relationship('Appointment', back_populates='client')


# TAGS (ISSUE / METHOD)
class Issue(db.Model):
    __tablename__ = 'issue'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True)
    label = db.Column(db.String(64))


class SpecialistIssue(db.Model):
    __tablename__ = 'specialist_issue'

    specialist_id = db.Column(db.Integer, db.ForeignKey('specialist.id'), primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), primary_key=True)


class Method(db.Model):
    __tablename__ = 'method'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True)
    label = db.Column(db.String(64))


class SpecialistMethod(db.Model):
    __tablename__ = 'specialist_method'

    specialist_id = db.Column(db.Integer, db.ForeignKey('specialist.id'), primary_key=True)
    method_id = db.Column(db.Integer, db.ForeignKey('method.id'), primary_key=True)



# SLOT (Cal.com)
class Slot(db.Model):
    __tablename__ = 'slot'

    id = db.Column(db.Integer, primary_key=True)
    specialist_id = db.Column(db.Integer, db.ForeignKey('specialist.id'))

    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)

    external_id = db.Column(db.String)  # Cal.com ID
    provider = db.Column(db.String, default='cal.com')

    specialist = db.relationship('Specialist', back_populates='slots')
    appointments = db.relationship('Appointment', back_populates='slot')



# APPOINTMENT
class AppointmentStatus(db.Model):
    __tablename__ = 'appointment_status'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True)
    label = db.Column(db.String(32))


class Appointment(db.Model):
    __tablename__ = 'appointment'

    id = db.Column(db.Integer, primary_key=True)

    slot_id = db.Column(db.Integer, db.ForeignKey('slot.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    status_id = db.Column(db.Integer, db.ForeignKey('appointment_status.id'))

    external_booking_id = db.Column(db.String)  # Cal.com booking ID
    booking_provider = db.Column(db.String, default='cal.com')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    slot = db.relationship('Slot', back_populates='appointments')
    client = db.relationship('Client', back_populates='appointments')
    status = db.relationship('AppointmentStatus')

    payment = db.relationship('Payment', uselist=False, back_populates='appointment')


# PAYMENT (YooKassa)
class Payment(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.Integer, primary_key=True)

    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'))

    provider = db.Column(db.String(32))  # yookassa
    provider_payment_id = db.Column(db.String, unique=True)

    amount = db.Column(db.Integer)
    currency = db.Column(db.String(8))

    status = db.Column(db.String(32))  # pending / succeeded / canceled

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)

    appointment = db.relationship('Appointment', back_populates='payment')



# CONSENTS

class ConsentType(db.Model):
    __tablename__ = 'consent_type'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True)
    label = db.Column(db.String(64))


class Consent(db.Model):
    __tablename__ = 'consent'

    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('consent_type.id'))

    version = db.Column(db.String(16))
    content_url = db.Column(db.String)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MemberConsent(db.Model):
    __tablename__ = 'member_consent'

    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), primary_key=True)
    consent_id = db.Column(db.Integer, db.ForeignKey('consent.id'), primary_key=True)

    accepted_at = db.Column(db.DateTime, default=datetime.utcnow)



    

