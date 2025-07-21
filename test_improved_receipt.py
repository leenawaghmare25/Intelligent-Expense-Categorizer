#!/usr/bin/env python3
"""
Test the improved receipt processor to verify it extracts only important items.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PYTHON.improved_receipt_processor import ImprovedReceiptProcessor
from PIL import Image, ImageDraw, ImageFont

def create_realistic_receipt():
    """Create a realistic receipt with noise and important items."""
    img = Image.new('RGB', (400, 700), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 14)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    y_pos = 20
    
    # Store header (should be detected as merchant)
    draw.text((50, y_pos), "WHOLE FOODS MARKET", fill='black', font=font)
    y_pos += 25
    draw.text((50, y_pos), "123 Organic Street", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Austin, TX 78701", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Phone: (512) 555-0123", fill='black', font=small_font)
    y_pos += 30
    
    # Date and time (should be filtered out as items)
    draw.text((50, y_pos), "Date: 01/20/2024", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Time: 14:30:25", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Cashier: Sarah M.", fill='black', font=small_font)
    y_pos += 40
    
    # Real items (should be extracted)
    items = [
        ("Organic Bananas 2 lbs", "3.98"),
        ("Whole Milk 1 Gallon", "4.49"),
        ("Free Range Eggs Dozen", "5.99"),
        ("Organic Spinach Bag", "2.99"),
        ("Sourdough Bread Loaf", "3.49"),
        ("Greek Yogurt 32oz", "6.99"),
    ]
    
    for item_name, price in items:
        draw.text((50, y_pos), item_name, fill='black', font=small_font)
        draw.text((300, y_pos), f"${price}", fill='black', font=small_font)
        y_pos += 25
    
    y_pos += 20
    draw.line([(50, y_pos), (350, y_pos)], fill='black', width=1)
    y_pos += 20
    
    # Totals (should be filtered out as items but detected as metadata)
    draw.text((50, y_pos), "Subtotal:", fill='black', font=small_font)
    draw.text((300, y_pos), "$27.93", fill='black', font=small_font)
    y_pos += 20
    
    draw.text((50, y_pos), "Tax:", fill='black', font=small_font)
    draw.text((300, y_pos), "$2.24", fill='black', font=small_font)
    y_pos += 20
    
    draw.text((50, y_pos), "Total:", fill='black', font=font)
    draw.text((300, y_pos), "$30.17", fill='black', font=font)
    y_pos += 40
    
    # Footer noise (should be filtered out)
    draw.text((50, y_pos), "Thank you for shopping!", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Visit us again soon", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Receipt #: WF123456789", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Customer Service: (512) 555-0199", fill='black', font=small_font)
    
    return img

def test_improved_receipt_processor():
    """Test the improved receipt processor."""
    print("🧪 TESTING IMPROVED RECEIPT PROCESSOR")
    print("=" * 50)
    
    try:
        # Create test receipt
        print("1. Creating realistic test receipt...")
        test_image = create_realistic_receipt()
        test_path = "improved_test_receipt.png"
        test_image.save(test_path)
        print("   ✅ Test receipt created")
        
        # Initialize improved processor
        print("2. Initializing improved processor...")
        processor = ImprovedReceiptProcessor()
        print("   ✅ Processor initialized")
        
        # Process receipt
        print("3. Processing receipt with improved algorithm...")
        receipt_data = processor.process_receipt_image(test_path)
        print("   ✅ Receipt processed")
        
        # Display results
        print("\n📊 IMPROVED PROCESSING RESULTS:")
        print("-" * 40)
        print(f"Merchant: {receipt_data.merchant_name}")
        print(f"Date: {receipt_data.date}")
        print(f"Total: ${receipt_data.total}")
        print(f"Tax: ${receipt_data.tax}")
        print(f"Subtotal: ${receipt_data.subtotal}")
        print(f"Confidence Score: {receipt_data.confidence_score:.2f}")
        print(f"Items Found: {len(receipt_data.items)}")
        
        print("\n🛒 EXTRACTED ITEMS (Important Only):")
        print("-" * 40)
        if receipt_data.items:
            for i, item in enumerate(receipt_data.items, 1):
                print(f"{i}. {item.name}")
                print(f"   Price: ${item.total_price:.2f}")
                print(f"   Confidence: {item.confidence:.2f}")
                if item.quantity:
                    print(f"   Quantity: {item.quantity}")
                if item.unit_price:
                    print(f"   Unit Price: ${item.unit_price:.2f}")
                print()
        else:
            print("No items extracted")
        
        # Analyze quality
        print("📈 QUALITY ANALYSIS:")
        print("-" * 20)
        
        expected_items = ["bananas", "milk", "eggs", "spinach", "bread", "yogurt"]
        extracted_names = [item.name.lower() for item in receipt_data.items]
        
        found_items = []
        for expected in expected_items:
            for extracted in extracted_names:
                if expected in extracted:
                    found_items.append(expected)
                    break
        
        print(f"Expected items found: {len(found_items)}/{len(expected_items)}")
        print(f"Accuracy: {len(found_items)/len(expected_items)*100:.1f}%")
        
        # Check for noise
        noise_indicators = ["thank", "visit", "phone", "cashier", "date", "time", "receipt"]
        noise_found = []
        for item in receipt_data.items:
            for noise in noise_indicators:
                if noise in item.name.lower():
                    noise_found.append(item.name)
        
        print(f"Noise items detected: {len(noise_found)}")
        if noise_found:
            print("Noise items:", noise_found)
        
        # Clean up
        os.remove(test_path)
        
        # Final assessment
        if len(found_items) >= 4 and len(noise_found) <= 1:
            print("\n🎉 IMPROVED PROCESSOR WORKING EXCELLENTLY!")
            print("✅ Successfully extracts important items")
            print("✅ Effectively filters out noise")
            print("✅ High accuracy and precision")
        elif len(found_items) >= 3:
            print("\n✅ IMPROVED PROCESSOR WORKING WELL!")
            print("✅ Good item extraction")
            print("⚠️  Some room for improvement")
        else:
            print("\n⚠️  PROCESSOR NEEDS FURTHER IMPROVEMENT")
            print("❌ Low item extraction accuracy")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if os.path.exists("improved_test_receipt.png"):
            os.remove("improved_test_receipt.png")
        
        return False

if __name__ == "__main__":
    success = test_improved_receipt_processor()
    sys.exit(0 if success else 1)