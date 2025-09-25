import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import random

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the smart AI processor
from app.services.smart_ai_processor import SmartAIProcessor
from app.db.database import get_db, init_db
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order, OrderItem

def init_sample_data(db: Session):
    """Initialize the database with sample data for testing."""
    # Check if we already have data
    if db.query(Customer).count() > 0:
        print("Database already contains sample data.")
        return
    
    print("Initializing sample data...")
    
    # Create sample customers
    cities = ["תל אביב", "ירושלים", "חיפה", "באר שבע", "נתניה"]
    products = ["מחשב נייד", "טלפון חכם", "מסך", "מקלדת", "עכבר"]
    
    # Add customers
    customers = []
    for i in range(1, 11):
        customer = Customer(
            name=f"לקוח {i}",
            email=f"customer{i}@example.com",
            city=random.choice(cities),
            join_date=datetime.now() - timedelta(days=random.randint(1, 365))
        )
        db.add(customer)
        customers.append(customer)
    
    db.commit()
    
    # Add products
    product_objs = []
    for i, product_name in enumerate(products, 1):
        product = Product(
            name=product_name,
            price=random.uniform(100, 5000),
            category=random.choice(["אלקטרוניקה", "משרדי", "גיימינג"]),
            in_stock=random.randint(0, 100)
        )
        db.add(product)
        product_objs.append(product)
    
    db.commit()
    
    # Add orders
    statuses = ["ממתין לתשלום", "מאושר", "נשלח", "הגיע ליעדו"]
    
    for i in range(1, 21):
        order = Order(
            customer_id=random.choice(customers).id,
            order_date=datetime.now() - timedelta(days=random.randint(1, 30)),
            status=random.choice(statuses)
        )
        db.add(order)
        db.flush()  # To get the order ID
        
        # Add order items
        num_items = random.randint(1, 4)
        for _ in range(num_items):
            product = random.choice(product_objs)
            item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=random.randint(1, 5),
                price=product.price * (1 - random.uniform(0, 0.3))  # Random discount up to 30%
            )
            db.add(item)
    
    db.commit()
    print("Sample data initialized successfully!")

def test_smart_ai():
    """Test the smart AI processor with sample questions."""
    # Initialize database
    db = next(get_db())
    
    try:
        # Initialize sample data
        init_sample_data(db)
        
        # Initialize the smart AI processor
        print("\nInitializing Smart AI Processor...")
        ai_processor = SmartAIProcessor(db)
        
        # Sample questions to test
        questions = [
            "הראה לי את כל הלקוחות",
            "כמה הזמנות יש בסך הכל?",
            "מהי ההכנסה הכוללת מההזמנות?",
            "מהו המוצר הכי פופולרי?",
            "הצג את ההזמנות האחרונות",
            "מהי העיר עם הכי הרבה לקוחות?",
            "הצג את ההכנסות לפי חודש",
            "מי הלקוח עם הכי הרבה הזמנות?",
            "מהו סכום המכירות הממוצע להזמנה?",
            "הצג את המוצרים שאוזלים מהמלאי"
        ]
        
        # Process each question
        for question in questions:
            print(f"\n{'='*80}")
            print(f"שאלה: {question}")
            print(f"{'='*80}")
            
            # Process the question
            result = ai_processor.process_question(question)
            
            # Print the results
            if result['success']:
                print(f"\nתשובה: {result['response']}")
                
                if 'sql' in result:
                    print(f"\nשאילתת SQL:\n{result['sql']}")
                
                if 'visualization' in result and result['visualization']:
                    viz = result['visualization']
                    print(f"\nהצעת ויזואליזציה: {viz['type']} - {viz.get('title', '')}")
                    print(f"ציר X: {viz.get('x_axis', 'N/A')}")
                    print(f"ציר Y: {viz.get('y_axis', 'N/A')}")
                
                if 'data' in result and result['data']:
                    data = result['data']
                    print(f"\nנתונים ({len(data)} שורות):")
                    # Print column headers
                    if data:
                        columns = list(data[0].keys())
                        print(" | ".join(columns))
                        print("-" * (sum(len(str(c)) for c in columns) + 3 * (len(columns) - 1)))
                        # Print first 3 rows
                        for row in data[:3]:
                            print(" | ".join(str(row.get(col, '')) for col in columns))
                        if len(data) > 3:
                            print(f"... ועוד {len(data) - 3} שורות")
            else:
                print(f"\nשגיאה: {result.get('error', 'שגיאה לא ידועה')}")
                print(f"תגובה: {result.get('response', 'אין פרטים נוספים')}")
            
            print("\n" + "-"*80)
    
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_smart_ai()
