# ID Card Field Extraction Pipeline

Automated extraction of structured information from Isaziland ID card images using OpenAI Vision API and agentic workflows.

## Overview

This project implements a multi-stage agentic pipeline that automatically extracts 8 structured fields from ID card images:
- Surname
- Given Names
- ID Number
- Date of Birth
- Gender
- Issue Date
- Expiry Date
- Issuing Authority

The system achieves high accuracy through intelligent preprocessing, multi-stage validation, and automated error correction.

## Features

- ✅ **Automated Extraction**: Uses OpenAI GPT-4V/GPT-4o for intelligent field extraction
- ✅ **Image Preprocessing**: Automatic rotation correction, noise reduction, and enhancement
- ✅ **Multi-Agent Architecture**: Specialized agents for extraction, validation, and correction
- ✅ **Robust Validation**: Format validation, business rules, and consistency checks
- ✅ **Error Correction**: Automatic re-extraction of failed fields
- ✅ **Batch Processing**: Process multiple images efficiently
- ✅ **Comprehensive Logging**: Detailed logs for debugging and monitoring
- ✅ **Confidence Scoring**: Quality metrics for each extraction

## Requirements

### System Requirements
- Python 3.9 or higher
- Internet connection (for OpenAI API)
- 8GB RAM minimum
- No GPU required

### Dependencies

```
openai>=1.0.0
opencv-python>=4.8.0
pillow>=10.0.0
numpy>=1.24.0
pydantic>=2.0.0
```

## Installation

### 1. Clone or Download the Project

```bash
# If using git
git clone <repository-url>
cd id-card-extraction

# Or download and extract the ZIP file
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up OpenAI API Key

You need an OpenAI API key with access to GPT-4V or GPT-4o.

**Option A: Environment Variable**
```bash
# On Windows (Command Prompt)
set OPENAI_API_KEY=your-api-key-here

# On Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"

# On macOS/Linux
export OPENAI_API_KEY="your-api-key-here"
```

**Option B: .env File**
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your-api-key-here
```

**Option C: Command Line Argument**
```bash
python extract_pipeline.py image.jpg --api-key your-api-key-here
```

## Usage

### Quick Start

Process a single ID card image:

```bash
python extract_pipeline.py path/to/id_card.jpg
```

Output will be saved to `output/id_card.json`

### Command Line Options

```bash
# Basic usage
python extract_pipeline.py <image_path>

# Specify output directory
python extract_pipeline.py image.jpg --output results/

# Skip preprocessing (if image is already clean)
python extract_pipeline.py image.jpg --no-preprocess

# Batch process directory of images
python extract_pipeline.py images_folder/ --batch

# Provide API key directly
python extract_pipeline.py image.jpg --api-key sk-...
```

### Batch Processing

Process all images in a directory:

```bash
python extract_pipeline.py isaziland_id_dataset/images/ --batch --output results/
```

This will:
- Process all `.jpg`, `.jpeg`, and `.png` files
- Save individual results as JSON files
- Generate a `batch_summary.json` with statistics

### Using as a Python Library

```python
from extract_pipeline import IDCardExtractionPipeline

# Initialize pipeline
pipeline = IDCardExtractionPipeline()

# Process single image
result = pipeline.process_image("id_card.jpg")

# Access extracted fields
print(result.fields)
print(f"Status: {result.status}")
print(f"Processing time: {result.processing_time:.2f}s")

# Batch processing
image_paths = ["id_1.jpg", "id_2.jpg", "id_3.jpg"]
summary = pipeline.process_batch(image_paths, output_dir="output")
```

## Output Format

### JSON Structure

Each processed image produces a JSON file with this exact format:

```json
{
  "surname": "SMITH",
  "given_names": "ADAM",
  "id_number": "IZA-870413-5-2761",
  "dob": "13 Apr 1987",
  "gender": "MALE",
  "issue_date": "12 Jan 2023",
  "expiry_date": "09 Jan 2033",
  "issuing_authority": "MINISTRY OF INTERNAL AFFAIRS"
}
```

### Format Requirements

- **surname, given_names, issuing_authority**: UPPERCASE text
- **id_number**: Format `IZA-YYMMDD-X-XXXX`
- **dob, issue_date, expiry_date**: Format `DD MMM YYYY` (e.g., "13 Apr 1987")
- **gender**: Either "MALE" or "FEMALE"

### Result Status

The pipeline assigns one of four statuses:

- **success**: All fields extracted and validated successfully
- **partial**: Most fields correct, minor issues
- **needs_review**: Multiple validation failures, requires human review
- **error**: Processing failed (exception occurred)

## Project Structure

```
id-card-extraction/
├── extract_pipeline.py          # Main pipeline implementation
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── ARCHITECTURE.md              # System design documentation
├── METHODOLOGY.md               # Approach and design decisions
├── RESULTS.md                   # Performance analysis
├── .env                         # API key (create this, not in git)
├── output/                      # Default output directory
│   └── batch_summary.json       # Batch processing results
├── tests/                       # Unit tests
│   ├── test_validation.py
│   ├── test_preprocessing.py
│   └── test_pipeline.py
└── extraction_pipeline.log      # Execution logs
```

## Examples

### Example 1: Single Image Processing

```bash
python extract_pipeline.py isaziland_id_dataset/images/id_1.jpg
```

**Output:**
```
Processing image: isaziland_id_dataset/images/id_1.jpg
ExtractionAgent: Starting field extraction
ValidationAgent: Starting validation
ValidationAgent: All validations passed
Pipeline completed: success (3.45s, 1 API calls)

Extraction complete!
Status: success
Processing time: 3.45s
API calls: 1

Extracted fields:
{
  "surname": "JOHNSON",
  "given_names": "SARAH MARIE",
  ...
}

Result saved to: output/id_1.json
```

### Example 2: Batch Processing

```bash
python extract_pipeline.py isaziland_id_dataset/images/ --batch
```

**Output:**
```
Found 200 images to process
Processing image 1/200: id_1.jpg
...
Batch processing complete:
  Total: 200
  Successful: 185
  Needs Review: 12
  Failed: 3
  Results saved to: output
```

### Example 3: Custom Output Directory

```bash
python extract_pipeline.py test_images/rotated_id.jpg --output my_results/
```

## Configuration

### Adjusting Pipeline Parameters

Edit the `Config` class in `extract_pipeline.py`:

```python
class Config:
    OPENAI_MODEL = "gpt-4o"  # or "gpt-4-vision-preview"
    TEMPERATURE = 0.0
    MAX_TOKENS = 1000
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    RATE_LIMIT_DELAY = 1
    
    # Confidence thresholds
    HIGH_CONFIDENCE = 0.9
    MEDIUM_CONFIDENCE = 0.7
    LOW_CONFIDENCE = 0.5
```

### Preprocessing Options

Disable preprocessing for clean images:
```bash
python extract_pipeline.py clean_image.jpg --no-preprocess
```

## Troubleshooting

### Common Issues

**1. "OpenAI API key not provided"**
- Solution: Set the `OPENAI_API_KEY` environment variable or use `--api-key` flag

**2. "Rate limit exceeded"**
- Solution: The pipeline includes automatic rate limiting, but if you hit OpenAI's limits, wait a few minutes or reduce batch size

**3. "Image not found"**
- Solution: Check the file path is correct and the file exists

**4. "Invalid JSON response"**
- Solution: This is usually temporary. The pipeline will retry automatically. Check logs for details.

**5. Low accuracy on rotated images**
- Solution: Ensure preprocessing is enabled (it's on by default)

### Viewing Logs

Detailed logs are saved to `extraction_pipeline.log`:

```bash
# View recent logs
tail -f extraction_pipeline.log

# Search for errors
grep ERROR extraction_pipeline.log

# View validation failures
grep "validation failure" extraction_pipeline.log
```

## Performance

### Expected Performance

Based on development set testing:

- **Field-Level Accuracy**: >90%
- **Per-Image Accuracy**: >75%
- **Processing Speed**: 3-8 seconds per image (depending on corrections needed)
- **API Cost**: $0.02-0.05 per image

### Optimization Tips

1. **Batch Processing**: Process multiple images to amortize overhead
2. **Disable Preprocessing**: For clean images, use `--no-preprocess`
3. **Adjust Rate Limiting**: Modify `RATE_LIMIT_DELAY` if you have higher API limits
4. **Cache Results**: The pipeline saves all results to avoid reprocessing

## Testing

### Run Unit Tests

```bash
# Install pytest if not already installed
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=extract_pipeline --cov-report=html

# Run specific test file
pytest tests/test_validation.py -v
```

### Manual Testing

Test on sample images with known ground truth:

```bash
# Test single image
python extract_pipeline.py test_data/sample_id.jpg

# Compare output with ground truth
diff output/sample_id.json test_data/sample_id_ground_truth.json
```

## API Costs

### Cost Estimation

- **GPT-4o**: ~$0.01-0.015 per image
- **GPT-4V**: ~$0.02-0.03 per image
- **With corrections**: Additional $0.01-0.02 per correction

### Cost Tracking

Monitor costs in batch summary:

```json
{
  "total_images": 100,
  "total_api_calls": 125,
  "estimated_cost": "$1.50-$2.50"
}
```

## Best Practices

1. **Test on Sample First**: Process 5-10 images before running large batches
2. **Review Failed Cases**: Check `needs_review` status images manually
3. **Monitor Logs**: Watch for patterns in validation failures
4. **Backup Results**: Save output directory before reprocessing
5. **Version Control**: Track changes to prompts and validation rules

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review logs in `extraction_pipeline.log`
3. See detailed documentation in `ARCHITECTURE.md` and `METHODOLOGY.md`
4. Contact the development team

## License

[Your License Here]

## Acknowledgments

- OpenAI for GPT-4 Vision API
- OpenCV community for image processing tools
- Pydantic for data validation

## Version History

- **v1.0.0** (2025-01): Initial release with multi-agent pipeline
  - OpenAI Vision API integration
  - Image preprocessing
  - Validation and correction agents
  - Batch processing support

## Citation

If you use this code in your research, please cite:

```
[Your citation format here]
```

---

**Last Updated**: January 2025  
**Maintainer**: [Your Name/Team]  
**Status**: Production Ready