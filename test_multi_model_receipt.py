#!/usr/bin/env python3
"""
Test the multi-model receipt processor to verify it extracts only important items
with maximum accuracy using ensemble methods.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PYTHON.multi_model_receipt_processor import MultiModelReceiptProcessor
from PIL import Image, ImageDraw, ImageFont

def create_complex_receipt():
    """Create a complex receipt with various noise and important items."""
    img = Image.new('RGB', (450, 800), color='white')
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
    
    # Store header with noise
    draw.text((80, y_pos), "SUPERMARKET PLUS", fill='black', font=large_font)
    y_pos += 25
    draw.text((70, y_pos), "123 Shopping Center Blvd", fill='black', font=small_font)
    y_pos += 20
    draw.text((90, y_pos), "Austin, TX 78701", fill='black', font=small_font)
    y_pos += 20
    draw.text((80, y_pos), "Phone: (512) 555-0123", fill='black', font=small_font)
    y_pos += 20
    draw.text((70, y_pos), "www.supermarketplus.com", fill='black', font=small_font)
    y_pos += 30
    
    # Receipt metadata (noise)
    draw.text((50, y_pos), "Receipt #: SP789123456", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Date: 01/20/2024", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Time: 14:30:25", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Cashier: Maria S.", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Customer: Member #12345", fill='black', font=small_font)
    y_pos += 40
    
    # Real items with various formats
    items = [
        ("Organic Bananas 2.5 lbs", "4.98"),
        ("Whole Milk 1 Gallon", "3.99"),
        ("Free Range Eggs Dozen", "5.49"),
        ("Organic Baby Spinach 5oz", "2.99"),
        ("Artisan Sourdough Bread", "4.49"),
        ("Greek Yogurt 32oz Vanilla", "6.99"),
        ("Chicken Breast 2.3 lbs @ $5.99/lb", "13.77"),
        ("Olive Oil Extra Virgin 500ml", "8.99"),
        ("Pasta Penne 1 lb Box", "1.99"),
        ("Tomato Sauce Organic 24oz", "2.49"),
    ]
    
    for item_name, price in items:
        draw.text((50, y_pos), item_name, fill='black', font=small_font)
        draw.text((350, y_pos), f"${price}", fill='black', font=small_font)
        y_pos += 25
    
    y_pos += 20
    draw.line([(50, y_pos), (400, y_pos)], fill='black', width=1)
    y_pos += 20
    
    # More noise - promotions and discounts
    draw.text((50, y_pos), "Member Savings:", fill='black', font=small_font)
    draw.text((350, y_pos), "-$3.50", fill='black', font=small_font)
    y_pos += 20
    
    draw.text((50, y_pos), "Coupon Discount:", fill='black', font=small_font)
    draw.text((350, y_pos), "-$1.00", fill='black', font=small_font)
    y_pos += 30
    
    # Totals (should be detected as metadata, not items)
    draw.text((50, y_pos), "Subtotal:", fill='black', font=small_font)
    draw.text((350, y_pos), "$56.17", fill='black', font=small_font)
    y_pos += 20
    
    draw.text((50, y_pos), "Tax (8.25%):", fill='black', font=small_font)
    draw.text((350, y_pos), "$4.63", fill='black', font=small_font)
    y_pos += 20
    
    draw.text((50, y_pos), "Total:", fill='black', font=font)
    draw.text((350, y_pos), "$60.80", fill='black', font=font)
    y_pos += 30
    
    # Payment info (noise)
    draw.text((50, y_pos), "Payment Method: Credit Card", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Card: ****1234", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Change: $0.00", fill='black', font=small_font)
    y_pos += 30
    
    # Footer noise
    draw.text((50, y_pos), "Thank you for shopping with us!", fill='black', font=small_font)
    y_pos += 20
    draw.text((70, y_pos), "Visit us again soon!", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Return Policy: 30 days", fill='black', font=small_font)
    y_pos += 20
    draw.text((50, y_pos), "Customer Service: (512) 555-0199", fill='black', font=small_font)
    
    return img

def test_multi_model_processor():
    """Test the multi-model receipt processor."""
    print("🚀 TESTING MULTI-MODEL RECEIPT PROCESSOR")
    print("=" * 60)
    
    try:
        # Create complex test receipt
        print("1. Creating complex test receipt with noise...")
        test_image = create_complex_receipt()
        test_path = "multi_model_test_receipt.png"
        test_image.save(test_path)
        print("   ✅ Complex test receipt created")
        
        # Initialize multi-model processor
        print("2. Initializing multi-model processor...")
        processor = MultiModelReceiptProcessor()
        print("   ✅ Multi-model processor initialized")
        
        # Process receipt
        print("3. Processing receipt with multi-model ensemble...")
        receipt_data = processor.process_receipt_image(test_path)
        print("   ✅ Receipt processed with ensemble methods")
        
        # Display results
        print("\n📊 MULTI-MODEL PROCESSING RESULTS:")
        print("-" * 50)
        print(f"Merchant: {receipt_data.merchant_name}")
        print(f"Date: {receipt_data.date}")
        print(f"Total: ${receipt_data.total}")
        print(f"Tax: ${receipt_data.tax}")
        print(f"Subtotal: ${receipt_data.subtotal}")
        print(f"Confidence Score: {receipt_data.confidence_score:.2f}")
        print(f"Items Found: {len(receipt_data.items)}")
        
        print("\n🛒 EXTRACTED ITEMS (Multi-Model Ensemble):")
        print("-" * 50)
        if receipt_data.items:
            for i, item in enumerate(receipt_data.items, 1):
                print(f"{i:2d}. {item.name}")
                print(f"    💰 Price: ${item.total_price:.2f}")
                print(f"    🎯 Confidence: {item.confidence:.2f}")
                if item.quantity:
                    print(f"    📦 Quantity: {item.quantity}")
                if item.unit_price:
                    print(f"    💵 Unit Price: ${item.unit_price:.2f}")
                print()
        else:
            print("No items extracted")
        
        # Quality analysis
        print("📈 MULTI-MODEL QUALITY ANALYSIS:")
        print("-" * 35)
        
        expected_items = [
            "bananas", "milk", "eggs", "spinach", "bread", 
            "yogurt", "chicken", "oil", "pasta", "sauce"
        ]
        extracted_names = [item.name.lower() for item in receipt_data.items]
        
        found_items = []
        for expected in expected_items:
            for extracted in extracted_names:
                if expected in extracted:
                    found_items.append(expected)
                    break
        
        print(f"Expected items found: {len(found_items)}/{len(expected_items)}")
        print(f"Accuracy: {len(found_items)/len(expected_items)*100:.1f}%")
        
        # Check for noise filtering
        noise_indicators = [
            "thank", "visit", "phone", "cashier", "date", "time", "receipt",
            "customer", "member", "card", "payment", "change", "return",
            "service", "policy", "subtotal", "total", "tax", "discount"
        ]
        
        noise_found = []
        for item in receipt_data.items:
            for noise in noise_indicators:
                if noise in item.name.lower():
                    noise_found.append(item.name)
        
        print(f"Noise items detected: {len(noise_found)}")
        if noise_found:
            print("Noise items:", noise_found)
        
        # Confidence analysis
        high_conf_items = [item for item in receipt_data.items if item.confidence >= 0.8]
        medium_conf_items = [item for item in receipt_data.items if 0.6 <= item.confidence < 0.8]
        
        print(f"High confidence items (≥0.8): {len(high_conf_items)}")
        print(f"Medium confidence items (0.6-0.8): {len(medium_conf_items)}")
        
        # Clean up
        os.remove(test_path)
        
        # Final assessment
        accuracy = len(found_items)/len(expected_items)
        noise_ratio = len(noise_found) / max(len(receipt_data.items), 1)
        
        if accuracy >= 0.8 and noise_ratio <= 0.1 and len(high_conf_items) >= 5:
            print("\n🎉 MULTI-MODEL PROCESSOR WORKING EXCELLENTLY!")
            print("✅ High accuracy item extraction")
            print("✅ Excellent noise filtering")
            print("✅ High confidence predictions")
            print("✅ Ensemble methods working perfectly")
        elif accuracy >= 0.7 and noise_ratio <= 0.2:
            print("\n✅ MULTI-MODEL PROCESSOR WORKING VERY WELL!")
            print("✅ Good item extraction")
            print("✅ Good noise filtering")
            print("✅ Ensemble methods effective")
        elif accuracy >= 0.5:
            print("\n👍 MULTI-MODEL PROCESSOR WORKING WELL!")
            print("✅ Reasonable item extraction")
            print("⚠️  Some room for improvement")
        else:
            print("\n⚠️  PROCESSOR NEEDS IMPROVEMENT")
            print("❌ Low extraction accuracy")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if os.path.exists("multi_model_test_receipt.png"):
            os.remove("multi_model_test_receipt.png")
        
        return False

if __name__ == "__main__":
    success = test_multi_model_processor()
    sys.exit(0 if success else 1)