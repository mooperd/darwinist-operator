from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Enum
from sqlalchemy.orm import relationship, sessionmaker, scoped_session

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from flask_login import UserMixin

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2

# Define the declarative base
Base = declarative_base()

# Database connection string (adjust as necessary)
engine = create_engine(
    'postgresql+psycopg2://darwinist:darwinist@localhost/darwinist',
    pool_size=10,  # Max number of connections in the pool
    max_overflow=20  # Max number of extra connections when the pool is full
    )

# Create a configured "Session" class
Session = scoped_session(sessionmaker(bind=engine, expire_on_commit=False))

def create_all():
    # Import models here to ensure they are registered with Base.metadata
    Base.metadata.create_all(engine)


class User(Base, UserMixin):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="vendor")  # e.g., 'vendor', 'superuser'
    api_token = Column(String, unique=True)

    # Generate password hash
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    # Check password validity
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Generate and set a new API token
    def generate_api_token(self):
        self.api_token = secrets.token_hex(32)

    # This method is required by Flask-Login to identify the user
    def get_id(self):
        return str(self.user_id)  # Must return a string


class Vendor(Base):
    __tablename__ = 'vendors'
    vendor_id = Column(Integer, primary_key=True)
    vendor_name = Column(String)
    contact_email = Column(String)
    website = Column(String)
    products = relationship('Product', back_populates='vendor')


class Product(Base):
    __tablename__ = 'products'
    product_id = Column(Integer, primary_key=True)
    product_name = Column(String)
    description = Column(String)
    dicom_output = Column(Boolean)
    vendor_id = Column(Integer, ForeignKey('vendors.vendor_id'))
    vendor = relationship('Vendor', back_populates='products')
    approvals = relationship('Approval', back_populates='product')
    clinical_trials = relationship('ClinicalTrial', back_populates='product')


class Modality(Base):
    __tablename__ = 'modalities'
    modality_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    approvals = relationship('Approval', back_populates='modality')


class BodyPart(Base):
    __tablename__ = 'body_parts'
    body_part_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    approvals = relationship('Approval', back_populates='body_part')


class Pathology(Base):
    __tablename__ = 'pathologies'
    pathology_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    approvals = relationship('Approval', back_populates='pathology')


class RegulatoryBody(Base):
    __tablename__ = 'regulatory_bodies'
    regulatory_body_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    approvals = relationship('Approval', back_populates='regulatory_body')


class Approval(Base):
    __tablename__ = 'approvals'
    approval_id = Column(Integer, primary_key=True)
    approval_date = Column(String)  # Use Date type if date format is consistent
    approval_status = Column(Boolean)
    id_code = Column(String)  # Corresponds to 'id' in the JSON
    product_id = Column(Integer, ForeignKey('products.product_id'))
    pathology_id = Column(Integer, ForeignKey('pathologies.pathology_id'))
    modality_id = Column(Integer, ForeignKey('modalities.modality_id'))
    body_part_id = Column(Integer, ForeignKey('body_parts.body_part_id'))
    regulatory_body_id = Column(Integer, ForeignKey('regulatory_bodies.regulatory_body_id'))

    product = relationship('Product', back_populates='approvals')
    pathology = relationship('Pathology', back_populates='approvals')
    modality = relationship('Modality', back_populates='approvals')
    body_part = relationship('BodyPart', back_populates='approvals')
    regulatory_body = relationship('RegulatoryBody', back_populates='approvals')


class ClinicalTrial(Base):
    __tablename__ = 'clinical_trials'

    trial_id = Column(Integer, primary_key=True)
    trial_name = Column(String, nullable=False)
    description = Column(String)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    trial_type = Column(Enum('formal', 'informal', name='trial_type_enum'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.product_id'))

    # Relationships
    product = relationship('Product', back_populates='clinical_trials')
    enrollments = relationship('TrialEnrollment', back_populates='trial')
    standards = relationship('ClinicalTrialStandard', back_populates='trial')


class Patient(Base):
    __tablename__ = 'patients'

    patient_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(Enum('Male', 'Female', 'Other', name='gender_enum'))
    medical_history = Column(String)

    # Relationships
    enrollments = relationship('TrialEnrollment', back_populates='patient')


class TrialEnrollment(Base):
    __tablename__ = 'trial_enrollments'

    enrollment_id = Column(Integer, primary_key=True)
    trial_id = Column(Integer, ForeignKey('clinical_trials.trial_id'))
    patient_id = Column(Integer, ForeignKey('patients.patient_id'))
    date_enrolled = Column(Date, nullable=False)
    image_processing_job_id = Column(String, nullable=True)

    # Relationships
    trial = relationship('ClinicalTrial', back_populates='enrollments')
    patient = relationship('Patient', back_populates='enrollments')
    results = relationship('TrialResult', back_populates='enrollment')


class TrialResult(Base):
    __tablename__ = 'trial_results'

    result_id = Column(Integer, primary_key=True)
    enrollment_id = Column(Integer, ForeignKey('trial_enrollments.enrollment_id'))
    outcome = Column(String)
    date_of_result = Column(Date, nullable=False)
    additional_data = Column(String)

    # Relationships
    enrollment = relationship('TrialEnrollment', back_populates='results')


class Standard(Base):
    __tablename__ = 'standards'

    standard_id = Column(Integer, primary_key=True)
    standard_name = Column(String, nullable=False)
    description = Column(String)

    # Relationships
    trials = relationship('ClinicalTrialStandard', back_populates='standard')


class ClinicalTrialStandard(Base):
    __tablename__ = 'clinical_trial_standards'

    id = Column(Integer, primary_key=True)
    trial_id = Column(Integer, ForeignKey('clinical_trials.trial_id'))
    standard_id = Column(Integer, ForeignKey('standards.standard_id'))

    # Relationships
    trial = relationship('ClinicalTrial', back_populates='standards')
    standard = relationship('Standard', back_populates='trials')