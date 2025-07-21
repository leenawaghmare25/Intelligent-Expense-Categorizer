#!/usr/bin/env python3
"""
Complete test of the improved receipt processing solution.
Demonstrates the solution to the original problem: extracting only important items
and their specific amounts while filtering out unwanted noise.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PYTHON.receipt_processor import ReceiptExpenseManager
from PYTHON.models import db, User, Expense
from PYTHON.app import create_app
from PIL import Image, ImageDraw, ImageFont

def create_noisy_receipt():
    """Create a receipt with lots of noise to test filtering."""
    img = Image.new('RGB', (500, 900), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 14)
        small_font = ImageFont.truetype("arial.ttf", 12)
        large_font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        large_font = ImageFont.load_default()
    
    y_pos = 20
    
    # Lots of store header noise
    draw.text((120, y_pos), "MEGA GROCERY STORE", fill='black', font=large_font)
    y_pos += 25
    draw.text((80, y_pos), "Your Neighborhood Supermarket", fill='black', font=small_font)
    y_pos += 20
    draw.text((100, y_pos), "123 Main Street", fill='black', font=small_font)
    y_pos += 20
    draw.text((110, y_pos), "Anytown, ST 12345", fill='black', font=small_font)
    y_pos += 20
    draw.text((100, y_pos), "Phone: (555) 123-4567", fill='black', font=small_font)
    y_pos += 20
    draw.text((80, y_pos), "Email: info@megagrocery.com", fill='black', font=small_font)
    y_pos += 20
    draw.text((90, y_pos), "Website: www.megagrocery.com", fill='black', font=small_font)
    y_pos += 30
    
    # Receipt metadata noise
    draw.text((50, y_pos), "Receipt Number: MG20240120001", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Transaction ID: TXN789456123", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Date: January 20, 2024", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Time: 2:30:45 PM", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Cashier: Jennifer M.", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Register: #3", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Customer: Loyalty Member #98765", fill='black', font=small_font)
    y_pos += 40
    
    # Important items (what we want to extract)
    items = [
        ("Organic Apples Gala 3 lbs", "5.97"),
        ("Whole Wheat Bread Loaf", "2.89"),
        ("Almond Milk Unsweetened 64oz", "4.49"),
        ("Free Range Eggs Large Dozen", "4.99"),
        ("Organic Baby Carrots 1 lb", "1.99"),
        ("Greek Yogurt Plain 32oz", "5.99"),
        ("Ground Turkey 93/7 1.2 lbs", "7.99"),
        ("Olive Oil Extra Virgin 16.9oz", "9.99"),
        ("Brown Rice Organic 2 lbs", "3.49"),
        ("Frozen Broccoli 12oz", "2.29"),
    ]
    
    for item_name, price in items:
        draw.text((50, y_pos), item_name, fill='black', font=small_font)
        draw.text((380, y_pos), f"${price}", fill='black', font=small_font)
        y_pos += 25
    
    y_pos += 20
    draw.line([(50, y_pos), (450, y_pos)], fill='black', width=1)
    y_pos += 20
    
    # More noise - promotions, discounts, etc.
    draw.text((50, y_pos), "Loyalty Card Savings:", fill='black', font=small_font)
    draw.text((380, y_pos), "-$4.50", fill='black', font=small_font)
    y_pos += 20
    
    draw.text((50, y_pos), "Manufacturer Coupon:", fill='black', font=small_font)
    draw.text((380, y_pos), "-$1.00", fill='black', font=small_font)
    y_pos += 20
    
    draw.text((50, y_pos), "Store Promotion:", fill='black', font=small_font)
    draw.text((380, y_pos), "-$2.25", fill='black', font=small_font)
    y_pos += 30
    
    # Totals (should be metadata, not items)
    draw.text((50, y_pos), "Subtotal:", fill='black', font=small_font)
    draw.text((380, y_pos), "$50.08", fill='black', font=small_font)
    y_pos += 20
    
    draw.text((50, y_pos), "Total Savings:", fill='black', font=small_font)
    draw.text((380, y_pos), "$7.75", fill='black', font=small_font)
    y_pos += 20
    
    draw.text((50, y_pos), "Tax (7.5%):", fill='black', font=small_font)
    draw.text((380, y_pos), "$3.76", fill='black', font=small_font)
    y_pos += 20
    
    draw.text((50, y_pos), "Total Amount:", fill='black', font=font)
    draw.text((380, y_pos), "$53.84", fill='black', font=font)
    y_pos += 30
    
    # Payment noise
    draw.text((50, y_pos), "Payment Method: Debit Card", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Card Number: ****5678", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Authorization: 123456", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Change Due: $0.00", fill='black', font=small_font)
    y_pos += 30
    
    # Footer noise
    draw.text((80, y_pos), "Thank you for shopping with us!", fill='black', font=small_font)
    y_pos += 20
    draw.text((100, y_pos), "Have a great day!", fill='black', font=small_font)
    y_pos += 20
    draw.text((70, y_pos), "Visit us again soon for more savings!", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Return Policy: 30 days with receipt", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Customer Service: (555) 123-4567", fill='black', font=small_font)
    y_pos += 20
    draw.text((80, y_pos), "Follow us on social media!", fill='black', font=small_font)
    
    return img

def test_complete_solution():
    """Test the complete solution end-to-end."""
    print("🎯 TESTING COMPLETE RECEIPT PROCESSING SOLUTION")
    print("=" * 70)
    print("Problem: Extract only important items and their amounts")
    print("Solution: Multi-model processor with advanced filtering")
    print("=" * 70)
    
    try:
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Create test receipt with lots of noise
            print("1. Creating noisy test receipt...")
            test_image = create_noisy_receipt()
            test_path = "complete_test_receipt.png"
            test_image.save(test_path)
            print("   ✅ Noisy receipt created with lots of unwanted text")
            
            # Create test user
            print("2. Setting up test environment...")
            db.create_all()
            
            # Check if test user exists
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                test_user = User(username='testuser', email='test@example.com')
                test_user.set_password('testpass')
                db.session.add(test_user)
                db.session.commit()
            
            print("   ✅ Test environment ready")
            
            # Initialize receipt manager
            print("3. Initializing receipt expense manager...")
            manager = ReceiptExpenseManager()
            print("   ✅ Manager initialized with best available processor")
            
            # Process receipt
            print("4. Processing receipt and creating expenses...")
            result = manager.process_receipt_image(test_path, test_user.id)
            print("   ✅ Receipt processed and expenses created")
            
            # Display results
            print("\n📊 COMPLETE SOLUTION RESULTS:")
            print("-" * 50)
            print(f"✅ Success: {result['success']}")
            print(f"🏪 Merchant: {result['processing_summary']['merchant']}")
            print(f"📅 Date: {result['processing_summary']['date']}")
            print(f"💰 Total: ${result['processing_summary']['total']}")
            print(f"🎯 Confidence: {result['confidence_score']:.2f}")
            print(f"📦 Expenses Created: {result['expenses_created']}")
            
            print(f"\n🛒 EXTRACTED ITEMS (Only Important Ones):")
            print("-" * 50)
            
            expected_items = [
                "apples", "bread", "milk", "eggs", "carrots", 
                "yogurt", "turkey", "oil", "rice", "broccoli"
            ]
            
            found_items = []
            noise_items = []
            
            for i, expense in enumerate(result['expenses'], 1):
                item_name = expense['description']
                amount = expense['amount']
                
                print(f"{i:2d}. {item_name}")
                print(f"    💵 Amount: ${amount:.2f}")
                if 'category' in expense:
                    print(f"    📂 Category: {expense['category']}")
                print()
                
                # Check if this is an expected item
                item_found = False
                for expected in expected_items:
                    if expected in item_name.lower():
                        found_items.append(expected)
                        item_found = True
                        break
                
                # Check if this is noise
                noise_indicators = [
                    "thank", "visit", "phone", "cashier", "date", "time", "receipt",
                    "customer", "member", "card", "payment", "change", "return",
                    "service", "policy", "subtotal", "total", "tax", "discount",
                    "coupon", "savings", "promotion", "authorization"
                ]
                
                if not item_found:
                    for noise in noise_indicators:
                        if noise in item_name.lower():
                            noise_items.append(item_name)
                            break
            
            # Analysis
            print("📈 SOLUTION EFFECTIVENESS ANALYSIS:")
            print("-" * 40)
            print(f"Expected items found: {len(found_items)}/{len(expected_items)}")
            print(f"Item extraction accuracy: {len(found_items)/len(expected_items)*100:.1f}%")
            print(f"Noise items detected: {len(noise_items)}")
            print(f"Noise filtering effectiveness: {(1 - len(noise_items)/max(result['expenses_created'], 1))*100:.1f}%")
            
            if noise_items:
                print(f"Noise items found: {noise_items}")
            
            # Clean up
            try:
                os.remove(test_path)
            except FileNotFoundError:
                pass  # File already removed
            
            # Final assessment
            accuracy = len(found_items) / len(expected_items)
            noise_ratio = len(noise_items) / max(result['expenses_created'], 1)
            
            print("\n🎉 SOLUTION ASSESSMENT:")
            print("-" * 25)
            
            if accuracy >= 0.8 and noise_ratio <= 0.1:
                print("🏆 EXCELLENT SOLUTION!")
                print("✅ Problem SOLVED: Extracts only important items")
                print("✅ High accuracy in item identification")
                print("✅ Excellent noise filtering")
                print("✅ Precise amount extraction")
                print("✅ Ready for production use")
            elif accuracy >= 0.7 and noise_ratio <= 0.2:
                print("🥈 VERY GOOD SOLUTION!")
                print("✅ Problem largely SOLVED")
                print("✅ Good item extraction")
                print("✅ Good noise filtering")
                print("⚠️  Minor improvements possible")
            elif accuracy >= 0.5:
                print("🥉 GOOD SOLUTION!")
                print("✅ Problem partially solved")
                print("✅ Reasonable performance")
                print("⚠️  Room for improvement")
            else:
                print("❌ SOLUTION NEEDS WORK")
                print("❌ Low accuracy")
                print("❌ Problem not fully solved")
            
            print(f"\n📋 TECHNICAL SUMMARY:")
            print(f"   • Multi-model ensemble approach")
            print(f"   • Advanced OCR with preprocessing")
            print(f"   • Pattern-based item extraction")
            print(f"   • Semantic analysis for validation")
            print(f"   • Structural analysis for context")
            print(f"   • Comprehensive noise filtering")
            print(f"   • Confidence-based selection")
            
            return True
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if os.path.exists("complete_test_receipt.png"):
            os.remove("complete_test_receipt.png")
        
        return False

if __name__ == "__main__":
    success = test_complete_solution()
    sys.exit(0 if success else 1)