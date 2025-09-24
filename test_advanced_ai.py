import sys
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import pandas as pd
from datetime import datetime, timedelta
import random

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the advanced AI processor
from app.services.advanced_ai_processor import AdvancedAIProcessor

# Initialize SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bi.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define sample models
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    join_date = Column(Date)
    city = Column(String)
    
    orders = relationship("Order", back_populates="customer")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    price = Column(Float)
    
    order_items = relationship("OrderItem", back_populates="product")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    order_date = Column(Date, index=True)
    status = Column(String)
    
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Float)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

def init_test_db():
    """Initialize the test database with sample data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session
    db = SessionLocal()
    
    try:
        # Check if we already have data
        if db.query(Customer).count() > 0:
            print("Test database already initialized with data.")
            return db
        
        print("Initializing test database with sample data...")
        
        # Create sample customers
        cities = ["תל אביב", "ירושלים", "חיפה", "באר שבע", "נתניה", "אשדוד", "פתח תקווה"]
        customers = []
        for i in range(1, 21):
            customer = Customer(
                name=f"לקוח {i}",
                email=f"customer{i}@example.com",
                join_date=datetime.now() - timedelta(days=random.randint(1, 365)),
                city=random.choice(cities)
            )
            customers.append(customer)
            db.add(customer)
        
        db.commit()
        
        # Create sample products
        products = []
        categories = ["אלקטרוניקה", "ביגוד", "מזון", "ספרים", "צעצועים"]
        for i in range(1, 11):
            product = Product(
                name=f"מוצר {i}",
                category=random.choice(categories),
                price=round(random.uniform(10, 1000), 2)
            )
            products.append(product)
            db.add(product)
        
        db.commit()
        
        # Create sample orders
        statuses = ["ממתין לתשלום", "מאושר", "נשלח", "הגיע ליעדו"]
        for i in range(1, 51):
            order_date = datetime.now() - timedelta(days=random.randint(1, 90))
            order = Order(
                customer_id=random.randint(1, 20),
                order_date=order_date,
                status=random.choice(statuses)
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            
            # Add items to order
            num_items = random.randint(1, 5)
            for _ in range(num_items):
                product = random.choice(products)
                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=random.randint(1, 5),
                    price=product.price
                )
                db.add(item)
            
            db.commit()
        
        print("Test database initialized successfully!")
        return db
    
    except Exception as e:
        print(f"Error initializing test database: {str(e)}")
        db.rollback()
        raise

def test_advanced_ai():
    """Test the advanced AI processor with sample queries."""
    # Initialize database and get session
    db = init_test_db()
    
    try:
        # Initialize the AI processor
        print("\nInitializing Advanced AI Processor...")
        ai_processor = AdvancedAIProcessor(db)
        
        # Sample questions to test
        questions = [
            "הראה לי את כל הלקוחות",
            "כמה הזמנות יש במערכת?",
            "מהו הסכום הכולל של כל ההזמנות?",
            "מהו המחיר הממוצע של המוצרים?",
            "הצג את ההזמנות האחרונות",
            "אילו מוצרים נמכרו הכי הרבה?",
            "מהי העיר עם הכי הרבה לקוחות?",
            "הצג את ההכנסות לפי חודש"
        ]
        
        # Process each question
        for question in questions:
            print(f"\n{'='*50}")
            print(f"שאלה: {question}")
            print(f"{'='*50}")
            
            # Process the question
            result = ai_processor.process_question(question)
            
            # Print the results
            print(f"\nתשובה: {result.get('response')}")
            
            if 'sql' in result:
                print(f"\nשאילתת SQL:\n{result['sql']}")
            
            if 'visualization' in result and result['visualization']:
                viz = result['visualization']
                print(f"\nויזואליזציה: {viz['type']} - {viz['title']}")
                if viz['type'] == 'table':
                    df = pd.DataFrame(viz['data'])
                    print("\nטבלת נתונים:")
                    print(df.head(5).to_string(index=False))
                    if len(df) > 5:
                        print(f"... ועוד {len(df) - 5} שורות")
            
            print("\n" + "-"*50)
    
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_advanced_ai()
