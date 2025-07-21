#!/usr/bin/env python3
"""
Debug the receipt processing to see what's happening.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PYTHON.improved_receipt_processor import ImprovedReceiptProcessor
from PIL import Image, ImageDraw, ImageFont

def create_simple_receipt():
    """Create a simple receipt for debugging."""
    img = Image.new('RGB', (400, 500), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    y_pos = 20
    
    # Store name
    draw.text((50, y_pos), "GROCERY STORE", fill='black', font=font)
    y_pos += 40
    
    # Simple items with clear prices
    draw.text((50, y_pos), "Milk 1 Gallon", fill='black', font=font)
    draw.text((300, y_pos), "$4.99", fill='black', font=font)
    y_pos += 30
    
    draw.text((50, y_pos), "Bread Loaf", fill='black', font=font)
    draw.text((300, y_pos), "$2.49", fill='black', font=font)
    y_pos += 30
    
    draw.text((50, y_pos), "Eggs Dozen", fill='black', font=font)
    draw.text((300, y_pos), "$3.29", fill='black', font=font)
    y_pos += 50
    
    # Total
    draw.text((50, y_pos), "Total:", fill='black', font=font)
    draw.text((300, y_pos), "$10.77", fill='black', font=font)
    
    return img

def debug_receipt_processing():
    """Debug the receipt processing step by step."""
    print("🔍 DEBUGGING RECEIPT PROCESSING")
    print("=" * 40)
    
    try:
        # Create simple test receipt
        print("1. Creating simple test receipt...")
        test_image = create_simple_receipt()
        test_path = "debug_receipt.png"
        test_image.save(test_path)
        print("   ✅ Test receipt created")
        
        # Initialize processor
        processor = ImprovedReceiptProcessor()
        
        # Step-by-step processing
        print("\n2. Processing image...")
        processed_image = processor.preprocess_image_advanced(test_path)
        print("   ✅ Image preprocessed")
        
        print("\n3. Extracting text...")
        text_data = processor.extract_text_with_confidence(processed_image)
        print(f"   ✅ Text extracted with {text_data['confidence']:.2f} confidence")
        
        print("\n📄 EXTRACTED TEXT:")
        print("-" * 20)
        for i, line in enumerate(text_data['lines']):
            print(f"{i+1:2d}: {line}")
        
        print("\n4. Processing each line for items...")
        lines = text_data['lines']
        line_confidences = text_data.get('line_confidences', [50] * len(lines))
        
        for line_idx, line in enumerate(lines):
            print(f"\nLine {line_idx+1}: '{line}'")
            
            # Check exclusion
            should_exclude = processor._should_exclude_line_smart(line)
            print(f"  Should exclude: {should_exclude}")
            
            if should_exclude:
                continue
            
            # Extract prices
            prices = processor._extract_prices_precise(line)
            print(f"  Prices found: {prices}")
            
            if not prices:
                continue
            
            # Extract item name
            item_name = processor._extract_item_name_smart(line, prices)
            print(f"  Item name: '{item_name}'")
            
            if not item_name:
                continue
            
            # Validate item
            is_valid = processor._is_valid_item_smart(item_name, line)
            print(f"  Is valid item: {is_valid}")
            
            if not is_valid:
                continue
            
            # Calculate confidence
            confidence = processor._calculate_item_confidence_smart(
                line, item_name, prices[-1], line_idx, line_confidences
            )
            print(f"  Confidence: {confidence:.2f}")
            
            if confidence >= 0.3:
                print(f"  ✅ WOULD EXTRACT: {item_name} - ${prices[-1]}")
            else:
                print(f"  ❌ LOW CONFIDENCE: {item_name} - ${prices[-1]}")
        
        # Clean up
        os.remove(test_path)
        
        return True
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if os.path.exists("debug_receipt.png"):
            os.remove("debug_receipt.png")
        
        return False

if __name__ == "__main__":
    debug_receipt_processing()