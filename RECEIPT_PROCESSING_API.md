# Receipt Processing API Documentation

## Overview

The Smart Expense Categorizer includes advanced receipt image processing capabilities using OpenCV and pytesseract. This system can automatically extract structured data from receipt images and create expense records in the user's profile.

## Features

### 🖼️ Image Processing
- **Multi-technique preprocessing** - Applies multiple image enhancement techniques and selects the best one
- **Automatic image optimization** - Resizes large images for optimal performance
- **Format support** - JPG, PNG, GIF, BMP, TIFF formats supported
- **Quality assessment** - OCR confidence scoring to ensure reliable extraction

### 🔍 Text Extraction
- **Advanced OCR** - Uses pytesseract with optimized configuration for receipts
- **Confidence scoring** - Provides reliability metrics for extracted text
- **Error handling** - Graceful degradation when OCR fails

### 📊 Data Structure Extraction
- **Merchant identification** - Recognizes common store names and brands
- **Date/time parsing** - Extracts transaction timestamps
- **Item parsing** - Identifies individual items with prices
- **Total calculation** - Extracts subtotal, tax, and total amounts
- **Receipt metadata** - Captures receipt numbers and other identifiers

### 🤖 AI Integration
- **Automatic categorization** - Uses ensemble ML models to categorize expenses
- **Category override** - Allows manual category specification
- **Confidence weighting** - Combines OCR and ML confidence scores

### 🗄️ Database Integration
- **User profiles** - Associates expenses with specific users
- **Metadata preservation** - Stores OCR confidence, merchant info, receipt numbers
- **Audit trails** - Tracks source of expense creation
- **Relationship management** - Proper foreign key relationships

## API Endpoints

### 1. Web Form Upload

**Endpoint:** `POST /upload-receipt`

**Description:** HTML form-based receipt upload with user interface

**Form Fields:**
- `receipt_image` (file, required) - Receipt image file
- `category_override` (select, optional) - Manual category override
- `notes` (textarea, optional) - Additional notes

**Response:** Redirects to expenses page with success/error message

### 2. API Upload

**Endpoint:** `POST /api/upload-receipt`

**Description:** RESTful API for programmatic receipt upload

**Request:**
```http
POST /api/upload-receipt
Content-Type: multipart/form-data
Authorization: Required (logged in user)

receipt_image: [binary file data]
category_override: "Dining Out" (optional)
```

**Response:**
```json
{
  "success": true,
  "receipt_data": {
    "merchant_name": "Starbucks Coffee",
    "date": "2024-01-20T08:45:00",
    "total": 15.80,
    "tax": 1.26,
    "subtotal": 14.54,
    "items": [
      {
        "name": "Grande Latte",
        "total_price": 5.45
      },
      {
        "name": "Blueberry Muffin", 
        "total_price": 3.25
      }
    ],
    "confidence_score": 0.85
  },
  "expenses_created": 2,
  "expenses": [
    {
      "id": "uuid-1",
      "description": "Starbucks Coffee - Grande Latte",
      "amount": 5.45,
      "predicted_category": "Dining Out",
      "confidence_score": 0.85,
      "source": "receipt_upload",
      "metadata": {
        "merchant": "Starbucks Coffee",
        "item_name": "Grande Latte",
        "confidence": 0.85
      }
    }
  ],
  "processing_summary": {
    "merchant": "Starbucks Coffee",
    "date": "2024-01-20T08:45:00",
    "total": 15.80,
    "items_count": 2
  }
}
```

### 3. Receipt History

**Endpoint:** `GET /receipt-history`

**Description:** View expenses created from receipt uploads

**Parameters:**
- `page` (int, optional) - Page number for pagination

**Response:** HTML page with receipt-based expenses

## Python API Usage

### Basic Usage

```python
from PYTHON.receipt_processor import process_receipt_image

# Process a receipt image
result = process_receipt_image(
    image_path="path/to/receipt.jpg",
    user_id=1,
    category_override="Dining Out"  # Optional
)

if result['success']:
    print(f"Created {result['expenses_created']} expenses")
    for expense in result['expenses']:
        print(f"- {expense['description']}: ${expense['amount']}")
```

### Advanced Usage

```python
from PYTHON.receipt_processor import ReceiptImageProcessor, ReceiptExpenseManager

# Initialize components
processor = ReceiptImageProcessor()
manager = ReceiptExpenseManager()

# Step-by-step processing
image_path = "receipt.jpg"

# 1. Preprocess image
processed_image = processor.preprocess_image(image_path)

# 2. Extract text
text, confidence = processor.extract_text(processed_image)

# 3. Parse structured data
receipt_data = processor.parse_receipt_data(text, confidence)

# 4. Create expenses
result = manager.process_receipt_image(image_path, user_id=1)
```

## Data Models

### ReceiptItem
```python
@dataclass
class ReceiptItem:
    name: str
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    category: Optional[str] = None
```

### ReceiptData
```python
@dataclass
class ReceiptData:
    merchant_name: Optional[str] = None
    merchant_address: Optional[str] = None
    date: Optional[datetime] = None
    time: Optional[str] = None
    items: List[ReceiptItem] = None
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None
    payment_method: Optional[str] = None
    receipt_number: Optional[str] = None
    confidence_score: float = 0.0
```

## Configuration

### Environment Variables

```bash
# File Upload Settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,bmp,tiff

# OCR Settings (optional)
TESSERACT_PATH=/usr/bin/tesseract  # If not in PATH
```

### Application Configuration

```python
# config.py
class Config:
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'}
```

## Error Handling

### Common Errors

1. **ValidationError** - Invalid input data
   ```json
   {"error": "Invalid file type. Only image files are allowed."}
   ```

2. **ModelNotFoundError** - ML models not available
   ```json
   {"error": "ML models not trained. Please run model training first."}
   ```

3. **DatabaseError** - Database operation failed
   ```json
   {"error": "Failed to store expenses in database."}
   ```

### Best Practices

1. **Image Quality**
   - Use well-lit, clear images
   - Avoid shadows and glare
   - Ensure text is readable
   - Crop to focus on receipt content

2. **File Size**
   - Keep images under 16MB
   - Resize large images before upload
   - Use appropriate compression

3. **Error Handling**
   - Always check the `success` field in responses
   - Handle network timeouts gracefully
   - Provide user feedback for errors

## Security Considerations

### File Upload Security
- File type validation using magic numbers
- Filename sanitization
- Size limits enforced
- Temporary file cleanup
- User authentication required

### Data Privacy
- User data isolation
- Secure file storage
- Metadata encryption options
- Audit logging

## Performance Optimization

### Image Processing
- Automatic image resizing for large files
- Multiple preprocessing techniques with best selection
- Efficient memory management
- Parallel processing capabilities

### Database Operations
- Batch expense creation
- Optimized queries with indexes
- Connection pooling
- Transaction management

## Testing

### Unit Tests
```bash
# Run receipt processing tests
python -m pytest tests/test_receipt_processor.py -v
```

### Integration Tests
```bash
# Run full system tests
python demo_receipt_processing.py
```

### Manual Testing
1. Upload various receipt types
2. Test different image qualities
3. Verify expense categorization
4. Check database consistency

## Troubleshooting

### Common Issues

1. **OCR Not Working**
   - Install tesseract: `apt-get install tesseract-ocr` (Linux) or `brew install tesseract` (Mac)
   - Check tesseract path in configuration
   - Verify image quality

2. **Low Confidence Scores**
   - Improve image quality
   - Ensure proper lighting
   - Check for image distortion

3. **Missing Dependencies**
   ```bash
   pip install opencv-python pytesseract Pillow imutils regex
   ```

4. **Database Errors**
   - Run database migrations
   - Check user permissions
   - Verify foreign key relationships

## Future Enhancements

### Planned Features
- [ ] Multi-language OCR support
- [ ] Receipt template learning
- [ ] Batch processing capabilities
- [ ] Mobile app integration
- [ ] Cloud storage integration
- [ ] Advanced analytics and reporting

### API Versioning
Current version: v1.0
- Backward compatibility maintained
- Deprecation notices for breaking changes
- Migration guides provided

---

For more information, see the main project documentation or contact the development team.