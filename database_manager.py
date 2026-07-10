import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
import shutil
import json

Base = declarative_base()

# --- DATABASE MODELS ---

class FieldDefinition(Base):
    __tablename__ = 'field_definitions'
    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False)    # e.g., "Phone Number"
    field_type = Column(String, nullable=False) # Text, Number, Date
    is_required = Column(Boolean, default=False)

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())

class CustomerValue(Base):
    __tablename__ = 'customer_values'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    field_id = Column(Integer, ForeignKey('field_definitions.id'))
    value = Column(String)

# --- HELPER FUNCTIONS ---

CONFIG_FILE = "config.json"

def save_config(base_path):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"base_path": base_path}, f)

def get_base_path():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                path = config.get("base_path")
                if path and os.path.exists(path):
                    return path
        except:
            pass
    
    # Default path
    path = os.path.join(os.path.expanduser("~"), "MyCustomerDatabases")
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def create_new_database(db_name, fields_list):
    """Creates a new folder and a new SQLite database with custom fields."""
    base_path = os.path.join(get_base_path(), db_name)
    customers_path = os.path.join(base_path, "customers")
    os.makedirs(customers_path, exist_ok=True)
    
    db_file = os.path.join(base_path, "data.db")
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    for f in fields_list:
        new_field = FieldDefinition(
            label=f['label'],
            field_type=f['type'],
            is_required=f.get('required', False)
        )
        session.add(new_field)
    
    session.commit()
    session.close()
    return base_path

def list_databases():
    """Returns a list of folder names that contain a data.db file."""
    root = get_base_path()
    if not os.path.exists(root): return []
    return [d for d in os.listdir(root) if os.path.isfile(os.path.join(root, d, "data.db"))]

def get_db_fields(db_name):
    """Connects to a specific database and returns its defined fields."""
    db_file = os.path.join(get_base_path(), db_name, "data.db")
    engine = create_engine(f"sqlite:///{db_file}")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    # Now FieldDefinition is properly defined in this file!
    fields = session.query(FieldDefinition).all()
    
    result = [{"id": f.id, "label": f.label, "type": f.field_type} for f in fields]
    session.close()
    return result

# ... (Keep everything else the same) ...

def add_customer(db_name, field_data_dict):
    db_path = os.path.join(get_base_path(), db_name)
    db_file = os.path.join(db_path, "data.db")
    engine = create_engine(f"sqlite:///{db_file}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Create the customer record
        new_customer = Customer()
        session.add(new_customer)
        session.flush() # Generates the ID

        # 2. Create the customer's physical folder
        # Path: MyCustomerDatabases/DbName/customers/ID/documents
        cust_folder = os.path.join(db_path, "customers", str(new_customer.id), "documents")
        os.makedirs(cust_folder, exist_ok=True)

        # 3. Save the custom values
        for field_id, value in field_data_dict.items():
            val_entry = CustomerValue(
                customer_id=new_customer.id,
                field_id=field_id,
                value=str(value)
            )
            session.add(val_entry)
        
        session.commit()
        return True
    except Exception as e:
        print(f"Error adding customer: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_customer_path(db_name, customer_id):
    """Returns the path to a customer's document folder."""
    return os.path.join(get_base_path(), db_name, "customers", str(customer_id), "documents")

def get_customers(db_name):
    """Returns all customers and their associated values."""
    db_file = os.path.join(get_base_path(), db_name, "data.db")
    engine = create_engine(f"sqlite:///{db_file}")
    Session = sessionmaker(bind=engine)
    session = Session()

    customers = session.query(Customer).all()
    field_defs = session.query(FieldDefinition).all()
    
    results = []
    for c in customers:
        # Build a row dictionary
        row = {"id": c.id}
        for f in field_defs:
            # Find the specific value for this customer and this field
            val = session.query(CustomerValue).filter_by(customer_id=c.id, field_id=f.id).first()
            row[f.id] = val.value if val else ""
        results.append(row)
    
    session.close()
    return results
def get_customers(db_name, search_query=""):
    """Returns customers, optionally filtered by a search query."""
    db_file = os.path.join(get_base_path(), db_name, "data.db")
    engine = create_engine(f"sqlite:///{db_file}")
    Session = sessionmaker(bind=engine)
    session = Session()

    field_defs = session.query(FieldDefinition).all()
    
    # Base query for customers
    customers_query = session.query(Customer)
    
    if search_query:
        # Search in the CustomerValue table for any value matching the query
        matching_cust_ids = session.query(CustomerValue.customer_id).filter(
            CustomerValue.value.like(f"%{search_query}%")
        ).distinct()
        customers_query = customers_query.filter(Customer.id.in_(matching_cust_ids))

    customers = customers_query.all()
    
    results = []
    for c in customers:
        row = {"id": c.id}
        for f in field_defs:
            val = session.query(CustomerValue).filter_by(customer_id=c.id, field_id=f.id).first()
            row[f.id] = val.value if val else ""
        results.append(row)
    
    session.close()
    return results

def delete_customer(db_name, customer_id):
    """Deletes customer from DB and removes their folder."""
    db_path = os.path.join(get_base_path(), db_name)
    db_file = os.path.join(db_path, "data.db")
    engine = create_engine(f"sqlite:///{db_file}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Delete from Database
        session.query(CustomerValue).filter_by(customer_id=customer_id).delete()
        session.query(Customer).filter_by(id=customer_id).delete()
        
        # 2. Delete Physical Folder
        cust_folder = os.path.join(db_path, "customers", str(customer_id))
        if os.path.exists(cust_folder):
            shutil.rmtree(cust_folder)
            
        session.commit()
        return True
    except Exception as e:
        print(f"Delete Error: {e}")
        session.rollback()
        return False
    finally:
        session.close()