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

    UserID = Column(Integer, primary_key=True)
    Username = Column(String, nullable=False, unique=True)
    Email = Column(String, nullable=False, unique=True)
    PasswordHash = Column(String, nullable=False)
    Role = Column(String, default="vendor")  # e.g., 'vendor', 'superuser'
    APIToken = Column(String, unique=True)

    # Generate password hash
    def set_password(self, password):
        self.PasswordHash = generate_password_hash(password, method='pbkdf2:sha256')

    # Check password validity
    def check_password(self, password):
        return check_password_hash(self.PasswordHash, password)

    # Generate and set a new API token
    def generate_api_token(self):
        self.APIToken = secrets.token_hex(32)

    # This method is required by Flask-Login to identify the user
    def get_id(self):
        return str(self.UserID)  # Must return a string

class Vendor(Base):
    __tablename__ = 'vendors'

    VendorID = Column(String, primary_key=True)
    VendorName = Column(String, nullable=False)
    ContactEmail = Column(String)
    VendorAddress = Column(String)
    Website = Column(String)

    # One-to-many relationship with products
    products = relationship('Product', back_populates='vendor_')


class Product(Base):
    __tablename__ = 'products'

    ProductID = Column(String, primary_key=True)
    ProductName = Column(String, nullable=False)
    Description = Column(String)
    ResultsDisplayedInIDS7 = Column(Boolean)
    DICOMOutput = Column(String)
    WorklistIntegration = Column(Boolean)
    PrePopulatedReports = Column(Boolean)
    ProductType = Column(String)

    VendorID = Column(String, ForeignKey('vendors.VendorID'))

    # Relationship to vendor
    vendor_ = relationship('Vendor', back_populates='products')

    # Relationships
    pathologies = relationship('ProductPathology', back_populates='product')
    approvals = relationship('RegulatoryApproval', back_populates='product_')
    clinical_trials = relationship('ClinicalTrial', back_populates='product')


class Pathology(Base):
    __tablename__ = 'pathologies'

    PathologyID = Column(String, primary_key=True)
    PathologyName = Column(String, nullable=False)

    # Many-to-many relationship with products via ProductPathology
    products = relationship('ProductPathology', back_populates='pathology')

# Junction Table linking products with pathologies.
class ProductPathology(Base):
    __tablename__ = 'product_pathologies'

    ProductPathologyID = Column(Integer, primary_key=True)
    ProductID = Column(String, ForeignKey('products.ProductID'))
    PathologyID = Column(String, ForeignKey('pathologies.PathologyID'))
    UseCase = Column(String)  # e.g., diagnostic, treatment

    # Relationships
    product = relationship('Product', back_populates='pathologies')
    pathology = relationship('Pathology', back_populates='products')


class RegulatoryApproval(Base):
    __tablename__ = 'regulatory_approvals'

    ApprovalID = Column(Integer, primary_key=True)
    ApprovalStatus = Column(String)
    ApprovalDate = Column(Date, nullable=False)
    ApprovedBy = Column(String)
    ProductID = Column(String, ForeignKey('products.ProductID'))
    PathologyID = Column(String, ForeignKey('pathologies.PathologyID'))

    # Relationships
    product_ = relationship('Product', back_populates='approvals')
    pathology_ = relationship('Pathology')


class ClinicalTrial(Base):
    __tablename__ = 'clinical_trials'

    TrialID = Column(Integer, primary_key=True)
    TrialName = Column(String, nullable=False)
    Description = Column(String)
    StartDate = Column(Date, nullable=False)
    EndDate = Column(Date)
    TrialType = Column(Enum('formal', 'informal', name='trial_type_enum'), nullable=False)
    ProductID = Column(String, ForeignKey('products.ProductID'))

    # Relationships
    product = relationship('Product', back_populates='clinical_trials')
    enrollments = relationship('TrialEnrollment', back_populates='trial')
    standards = relationship('ClinicalTrialStandard', back_populates='trial')


class Patient(Base):
    __tablename__ = 'patients'

    PatientID = Column(Integer, primary_key=True)
    Name = Column(String, nullable=False)
    Age = Column(Integer)
    Gender = Column(Enum('Male', 'Female', 'Other', name='gender_enum'))
    MedicalHistory = Column(String)

    # Relationships
    enrollments = relationship('TrialEnrollment', back_populates='patient')


class TrialEnrollment(Base):
    __tablename__ = 'trial_enrollments'

    EnrollmentID = Column(Integer, primary_key=True)
    TrialID = Column(Integer, ForeignKey('clinical_trials.TrialID'))
    PatientID = Column(Integer, ForeignKey('patients.PatientID'))
    DateEnrolled = Column(Date, nullable=False)
    ImageProcessingJobID = Column(String, nullable=True)

    # Relationships
    trial = relationship('ClinicalTrial', back_populates='enrollments')
    patient = relationship('Patient', back_populates='enrollments')
    results = relationship('TrialResult', back_populates='enrollment')


class TrialResult(Base):
    __tablename__ = 'trial_results'

    ResultID = Column(Integer, primary_key=True)
    EnrollmentID = Column(Integer, ForeignKey('trial_enrollments.EnrollmentID'))
    Outcome = Column(String)
    DateOfResult = Column(Date, nullable=False)
    AdditionalData = Column(String)

    # Relationships
    enrollment = relationship('TrialEnrollment', back_populates='results')


class Standard(Base):
    __tablename__ = 'standards'

    StandardID = Column(Integer, primary_key=True)
    StandardName = Column(String, nullable=False)
    Description = Column(String)

    # Relationships
    trials = relationship('ClinicalTrialStandard', back_populates='standard')


class ClinicalTrialStandard(Base):
    __tablename__ = 'clinical_trial_standards'

    ID = Column(Integer, primary_key=True)
    TrialID = Column(Integer, ForeignKey('clinical_trials.TrialID'))
    StandardID = Column(Integer, ForeignKey('standards.StandardID'))

    # Relationships
    trial = relationship('ClinicalTrial', back_populates='standards')
    standard = relationship('Standard', back_populates='trials')
