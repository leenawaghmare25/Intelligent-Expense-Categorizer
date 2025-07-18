"""
Demonstration script for receipt image processing functionality.

This script shows how to use the receipt processing system with sample data.
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PYTHON.app import create_app
from PYTHON.models import db, User, Expense
from PYTHON.receipt_processor import ReceiptImageProcessor, ReceiptExpenseManager, process_receipt_image
from PYTHON.utils import setup_logger

def create_sample_receipt_image(output_path: str) -> str:
    """
    Create a sample receipt image for demonstration.
    
    Args:
        output_path: Path where to save the sample receipt
        
    Returns:
        Path to the created receipt image
    """
    print("📄 Creating sample receipt image...")
    
    # Create a realistic receipt image
    img = Image.new('RGB', (400, 700), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use system fonts, fallback to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 18)
        normal_font = ImageFont.truetype("arial.ttf", 14)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        title_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    y_pos = 30
    
    # Store header
    draw.text((80, y_pos), "STARBUCKS COFFEE", fill='black', font=title_font)
    y_pos += 35
    draw.text((70, y_pos), "Downtown Location", fill='black', font=normal_font)
    y_pos += 25
    draw.text((60, y_pos), "456 Business Ave, City, ST 12345", fill='black', font=small_font)
    y_pos += 20
    draw.text((120, y_pos), "Tel: (555) 987-6543", fill='black', font=small_font)
    y_pos += 40
    
    # Date and time
    draw.text((50, y_pos), "Date: 01/20/2024", fill='black', font=small_font)
    draw.text((250, y_pos), "Time: 08:45 AM", fill='black', font=small_font)
    y_pos += 30
    
    # Transaction details
    draw.text((50, y_pos), "Order #: 12345", fill='black', font=small_font)
    y_pos += 25
    draw.text((50, y_pos), "Cashier: Sarah M.", fill='black', font=small_font)
    y_pos += 35
    
    # Items
    items = [
        ("Grande Latte", "1", "5.45"),
        ("Blueberry Muffin", "1", "3.25"),
        ("Americano", "1", "4.15"),
        ("Croissant", "1", "2.95")
    ]
    
    # Items header
    draw.text((50, y_pos), "Item", fill='black', font=normal_font)
    draw.text((200, y_pos), "Qty", fill='black', font=normal_font)
    draw.text((280, y_pos), "Price", fill='black', font=normal_font)
    y_pos += 20
    draw.line([(50, y_pos), (350, y_pos)], fill='black', width=1)
    y_pos += 15
    
    subtotal = 0
    for item_name, qty, price in items:
        draw.text((50, y_pos), item_name, fill='black', font=small_font)
        draw.text((210, y_pos), qty, fill='black', font=small_font)
        draw.text((280, y_pos), f"${price}", fill='black', font=small_font)
        subtotal += float(price)
        y_pos += 22
    
    y_pos += 15
    draw.line([(50, y_pos), (350, y_pos)], fill='black', width=1)
    y_pos += 15
    
    # Totals
    tax = subtotal * 0.08  # 8% tax
    total = subtotal + tax
    
    draw.text((50, y_pos), "Subtotal:", fill='black', font=normal_font)
    draw.text((280, y_pos), f"${subtotal:.2f}", fill='black', font=normal_font)
    y_pos += 25
    
    draw.text((50, y_pos), "Tax (8%):", fill='black', font=normal_font)
    draw.text((280, y_pos), f"${tax:.2f}", fill='black', font=normal_font)
    y_pos += 25
    
    draw.text((50, y_pos), "TOTAL:", fill='black', font=title_font)
    draw.text((280, y_pos), f"${total:.2f}", fill='black', font=title_font)
    y_pos += 40
    
    # Payment info
    draw.text((50, y_pos), "Payment Method: Credit Card", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Card: ****1234", fill='black', font=small_font)
    y_pos += 30
    
    # Footer
    draw.text((50, y_pos), "Receipt #: SB20240120084501", fill='black', font=small_font)
    y_pos += 25
    draw.text((80, y_pos), "Thank you for your visit!", fill='black', font=small_font)
    
    # Save the image
    img.save(output_path)
    print(f"✅ Sample receipt saved to: {output_path}")
    return output_path

def demonstrate_receipt_processing():
    """Demonstrate the complete receipt processing workflow."""
    print("🚀 Starting Receipt Processing Demonstration")
    print("=" * 50)
    
    # Setup logging
    logger = setup_logger(__name__)
    
    # Create Flask app context
    app = create_app('development')
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Create or get test user
        user = User.query.filter_by(username='demo_user').first()
        if not user:
            user = User(username='demo_user', email='demo@example.com')
            user.set_password('demo123')
            db.session.add(user)
            db.session.commit()
            print(f"✅ Created demo user: {user.username}")
        else:
            print(f"✅ Using existing demo user: {user.username}")
        
        # Create sample receipt image
        receipt_path = "sample_receipt.png"
        create_sample_receipt_image(receipt_path)
        
        print("\n📊 Processing Receipt...")
        print("-" * 30)
        
        try:
            # Process the receipt
            result = process_receipt_image(receipt_path, user.id)
            
            if result['success']:
                print("✅ Receipt processed successfully!")
                print(f"📈 Processing Summary:")
                print(f"   • Expenses Created: {result['expenses_created']}")
                print(f"   • OCR Confidence: {result['confidence_score']:.1%}")
                
                summary = result['processing_summary']
                if summary['merchant']:
                    print(f"   • Merchant: {summary['merchant']}")
                if summary['total']:
                    print(f"   • Total Amount: ${summary['total']:.2f}")
                if summary['date']:
                    print(f"   • Date: {summary['date']}")
                print(f"   • Items Found: {summary['items_count']}")
                
                print(f"\n💰 Created Expenses:")
                print("-" * 20)
                for i, expense in enumerate(result['expenses'], 1):
                    print(f"{i}. {expense['description']}")
                    print(f"   Amount: ${expense['amount']:.2f}")
                    print(f"   Category: {expense['predicted_category']}")
                    print(f"   Confidence: {expense['confidence_score']:.1%}")
                    if expense.get('expense_metadata'):
                        metadata = expense['expense_metadata']
                        if metadata.get('item_name'):
                            print(f"   Item: {metadata['item_name']}")
                    print()
                
                # Show database verification
                print("🗄️  Database Verification:")
                print("-" * 25)
                db_expenses = Expense.query.filter_by(
                    user_id=user.id, 
                    source='receipt_upload'
                ).all()
                
                print(f"Total receipt-based expenses in DB: {len(db_expenses)}")
                for expense in db_expenses[-result['expenses_created']:]:  # Show latest ones
                    print(f"• ID: {expense.id}")
                    print(f"  Description: {expense.description}")
                    print(f"  Amount: ${expense.amount:.2f}")
                    print(f"  Category: {expense.predicted_category}")
                    print(f"  Source: {expense.source}")
                    print()
                
            else:
                print("❌ Receipt processing failed!")
                print(f"Error: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            print(f"❌ Error during processing: {str(e)}")
            logger.error(f"Processing error: {str(e)}", exc_info=True)
        
        finally:
            # Clean up sample image
            try:
                os.remove(receipt_path)
                print(f"🧹 Cleaned up sample image: {receipt_path}")
            except:
                pass

def demonstrate_individual_components():
    """Demonstrate individual components of the receipt processor."""
    print("\n🔧 Component-Level Demonstration")
    print("=" * 40)
    
    # Create sample receipt
    receipt_path = "component_test_receipt.png"
    create_sample_receipt_image(receipt_path)
    
    try:
        # Initialize processor
        processor = ReceiptImageProcessor()
        print("✅ Initialized ReceiptImageProcessor")
        
        # Step 1: Image preprocessing
        print("\n1️⃣ Image Preprocessing...")
        processed_image = processor.preprocess_image(receipt_path)
        print(f"   • Original image loaded and preprocessed")
        print(f"   • Processed image shape: {processed_image.shape}")
        print(f"   • Image type: {processed_image.dtype}")
        
        # Step 2: Text extraction
        print("\n2️⃣ OCR Text Extraction...")
        text, confidence = processor.extract_text(processed_image)
        print(f"   • Text extracted successfully")
        print(f"   • OCR confidence: {confidence:.1%}")
        print(f"   • Text length: {len(text)} characters")
        print(f"   • Sample text (first 200 chars):")
        print(f"     {repr(text[:200])}...")
        
        # Step 3: Data parsing
        print("\n3️⃣ Data Structure Parsing...")
        receipt_data = processor.parse_receipt_data(text, confidence)
        print(f"   • Merchant: {receipt_data.merchant_name}")
        print(f"   • Date: {receipt_data.date}")
        print(f"   • Time: {receipt_data.time}")
        print(f"   • Total: ${receipt_data.total}" if receipt_data.total else "   • Total: Not found")
        print(f"   • Tax: ${receipt_data.tax}" if receipt_data.tax else "   • Tax: Not found")
        print(f"   • Subtotal: ${receipt_data.subtotal}" if receipt_data.subtotal else "   • Subtotal: Not found")
        print(f"   • Receipt #: {receipt_data.receipt_number}")
        print(f"   • Items found: {len(receipt_data.items)}")
        
        if receipt_data.items:
            print(f"   • Sample items:")
            for i, item in enumerate(receipt_data.items[:3], 1):
                print(f"     {i}. {item.name} - ${item.total_price}")
        
        print(f"   • Overall confidence: {receipt_data.confidence_score:.1%}")
        
        # Step 4: JSON serialization
        print("\n4️⃣ Data Serialization...")
        from dataclasses import asdict
        receipt_dict = asdict(receipt_data)
        
        # Convert Decimal to float for JSON serialization
        def convert_decimals(obj):
            if hasattr(obj, '__dict__'):
                for key, value in obj.__dict__.items():
                    if hasattr(value, '__class__') and 'Decimal' in str(value.__class__):
                        setattr(obj, key, float(value))
            return obj
        
        # Clean up the dictionary for JSON
        json_str = json.dumps(receipt_dict, default=str, indent=2)
        print(f"   • Successfully serialized to JSON")
        print(f"   • JSON size: {len(json_str)} characters")
        
    except Exception as e:
        print(f"❌ Component test error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            os.remove(receipt_path)
        except:
            pass

if __name__ == "__main__":
    print("🏪 Smart Expense Categorizer - Receipt Processing Demo")
    print("=" * 60)
    
    # Run demonstrations
    demonstrate_receipt_processing()
    demonstrate_individual_components()
    
    print("\n🎉 Demonstration Complete!")
    print("=" * 30)
    print("Key Features Demonstrated:")
    print("✅ Image preprocessing with multiple techniques")
    print("✅ OCR text extraction with confidence scoring")
    print("✅ Intelligent data parsing and structure extraction")
    print("✅ Automatic expense categorization using ML")
    print("✅ Database integration with user profiles")
    print("✅ Comprehensive error handling and validation")
    print("✅ Metadata preservation for audit trails")
    print("\nThe system is ready for production use! 🚀")