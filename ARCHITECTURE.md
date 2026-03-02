# System Architecture

## Table of Contents
1. [Overview](#overview)
2. [System Design](#system-design)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Agent Architecture](#agent-architecture)
6. [Technology Stack](#technology-stack)
7. [Design Patterns](#design-patterns)
8. [Performance Considerations](#performance-considerations)

## Overview

The ID Card Extraction Pipeline is built on a **multi-agent architecture** where specialized agents handle different stages of the extraction and validation process. This design provides modularity, maintainability, and allows for iterative refinement of extractions through validation and correction loops.

### Architecture Principles

1. **Separation of Concerns**: Each component has a single, well-defined responsibility
2. **Agent-Based Design**: Independent agents that can be developed and tested separately
3. **Fail-Safe Operation**: Graceful degradation with human-in-the-loop fallback
4. **Observability**: Comprehensive logging and metrics at each stage
5. **Cost Optimization**: Intelligent API usage with caching and targeted corrections

## System Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Input Layer                               │
│  (Image File Path → Validation → Queue Management)          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Preprocessing Layer                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Rotation   │→ │    Noise     │→ │   Contrast   │      │
│  │  Detection  │  │  Reduction   │  │  Enhancement │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenAI API Interface Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐      │
│  │ Rate Limiter │→ │  API Client  │→ │   Response  │      │
│  │              │  │   (GPT-4V)   │  │   Parser    │      │
│  └──────────────┘  └──────────────┘  └─────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent Layer                                │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Extraction  │→ │  Validation  │→ │  Correction  │      │
│  │   Agent     │  │    Agent     │  │    Agent     │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Output Layer                               │
│  (Format Compliance → JSON Generation → Result Storage)     │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Layers

#### 1. Input Layer
- **Responsibilities**: File I/O, path validation, image format verification
- **Components**: File loader, format validator, batch queue manager
- **Error Handling**: Invalid paths, unsupported formats, permission issues

#### 2. Preprocessing Layer
- **Responsibilities**: Image enhancement and normalization
- **Components**: 
  - Rotation detector and corrector
  - Noise reduction filters
  - Contrast enhancement (CLAHE)
  - Size optimization
- **Technology**: OpenCV, NumPy

#### 3. OpenAI API Interface Layer
- **Responsibilities**: Communication with OpenAI Vision API
- **Components**:
  - Rate limiter (prevents API throttling)
  - Retry logic with exponential backoff
  - Response parser and validator
  - Error handler
- **Technology**: OpenAI Python SDK

#### 4. Agent Layer
- **Responsibilities**: Intelligent extraction, validation, and correction
- **Components**: Three specialized agents (detailed below)
- **Coordination**: Orchestrated by main pipeline controller

#### 5. Output Layer
- **Responsibilities**: Result formatting and storage
- **Components**: JSON serializer, file writer, batch summarizer
- **Validation**: Schema compliance checking

## Component Architecture

### 1. ImagePreprocessor

```python
class ImagePreprocessor:
    """Handles all image preprocessing operations"""
    
    Methods:
    - load_image(path)          # Load image from file
    - detect_rotation(img)      # Detect skew angle
    - correct_rotation(img)     # Apply rotation correction
    - enhance_image(img)        # Apply filters
    - resize_for_api(img)       # Optimize size
    - preprocess(path)          # Complete pipeline
```

**Design Decisions:**
- Uses OpenCV for performance and reliability
- CLAHE for contrast enhancement (handles variable lighting)
- Hough line transform for rotation detection
- Bilateral filtering for noise reduction (preserves edges)

**Performance:**
- Average processing time: 0.5-1.5 seconds per image
- No external API calls (pure computation)
- Memory efficient with in-place operations

### 2. OpenAIVisionClient

```python
class OpenAIVisionClient:
    """Manages OpenAI API communication"""
    
    Methods:
    - encode_image(path)        # Convert to base64
    - rate_limit()              # Enforce rate limits
    - call_api(image, prompt)   # Make API request
    
    Features:
    - Exponential backoff retry (3 attempts)
    - Rate limiting (1 second minimum between calls)
    - Automatic error recovery
    - Request/response logging
```

**Design Decisions:**
- Singleton pattern for API client (shared connection pool)
- Base64 encoding for image transmission
- Configurable model selection (GPT-4o vs GPT-4V)
- Temperature=0.0 for deterministic outputs

**Error Handling:**
- Network errors → Retry with backoff
- Rate limit errors → Wait and retry
- Invalid response → Log and raise
- Timeout → Configurable timeout with retry

### 3. ExtractionAgent

```python
class ExtractionAgent:
    """Primary field extraction from images"""
    
    Methods:
    - create_extraction_prompt() # Generate extraction prompt
    - extract(image_path)        # Extract all fields
    
    Prompt Strategy:
    - Structured JSON output specification
    - Explicit format requirements
    - Example-based guidance
    - Error prevention instructions
```

**Prompt Engineering:**
```
Key elements:
1. Clear role definition ("expert OCR system")
2. Exact output format specification
3. Format requirements with examples
4. Constraints (UPPERCASE, date formats, etc.)
5. Error prevention (no markdown, no explanations)
```

**Output Processing:**
- JSON parsing with error recovery
- Markdown fence removal
- Whitespace normalization
- Validation of structure

### 4. ValidationAgent

```python
class ValidationAgent:
    """Rule-based validation of extracted fields"""
    
    Methods:
    - validate_id_number(value)    # Regex validation
    - validate_date(name, value)   # Format + logic
    - validate_gender(value)       # Enum validation
    - validate_text_field(name, value) # Completeness
    - validate_date_logic(data)    # Cross-field checks
    - validate_all(data)           # Complete validation
    
    Validation Rules:
    - Format patterns (regex)
    - Value constraints (enums)
    - Logical consistency (date ordering)
    - Completeness (non-empty fields)
```

**Validation Categories:**

1. **Format Validation**
   - ID Number: `IZA-\d{6}-\d-\d{4}`
   - Dates: `\d{2} [A-Z][a-z]{2} \d{4}`
   - Gender: `MALE|FEMALE`

2. **Logic Validation**
   - DOB < Issue Date < Expiry Date
   - Age at issue > 16 years
   - Issue date not in future
   - Expiry date > Issue date

3. **Completeness Validation**
   - All 8 fields present
   - Non-empty values
   - Proper capitalization

**No API Calls**: Pure Python logic, no cost

### 5. CorrectionAgent

```python
class CorrectionAgent:
    """Targeted correction of failed fields"""
    
    Methods:
    - create_correction_prompt(field, value, error)
    - correct_field(image, field, value, error)
    
    Strategy:
    - Focus on single field
    - Provide error context
    - Specific format guidance
    - Reduced token usage
```

**Correction Approach:**
- Targeted prompts (only failed field)
- Error-specific guidance
- Smaller context (cost optimization)
- Maximum 2 correction attempts per field

**Cost Optimization:**
- Only correct failed fields
- Reuse preprocessed image
- Limit correction iterations
- Skip if low confidence

### 6. IDCardExtractionPipeline

```python
class IDCardExtractionPipeline:
    """Main orchestrator coordinating all components"""
    
    Methods:
    - process_image(path, max_corrections, preprocess)
    - process_batch(paths, output_dir)
    
    Workflow:
    1. Preprocess image (if enabled)
    2. Extract fields (ExtractionAgent)
    3. Validate results (ValidationAgent)
    4. Correct failures (CorrectionAgent) - iterative
    5. Determine status
    6. Calculate metrics
    7. Save results
```

**Decision Logic:**

```
Extract → Validate → Decision Point
                           │
                ┌──────────┼──────────┐
                │          │          │
            All Valid   Some Invalid  Many Invalid
                │          │          │
              Success    Correct    Needs Review
                │          │          │
              Output    Re-validate   Flag
                           │
                      Max attempts?
                           │
                    ┌──────┴──────┐
                   Yes           No
                    │             │
                 Output      Retry Correct
```

## Data Flow

### Single Image Processing Flow

```
1. Input: "id_1.jpg"
   │
   ▼
2. Preprocessing (0.8s)
   ├─ Rotation: +2.3°
   ├─ Enhancement: CLAHE applied
   └─ Output: "preprocessed_id_1.jpg"
   │
   ▼
3. Extraction (3.2s, API Call #1)
   ├─ Prompt: 850 tokens
   ├─ Response: 250 tokens
   └─ Parsed: 8 fields extracted
   │
   ▼
4. Validation (0.1s, No API)
   ├─ Format checks: 8/8 passed
   ├─ Logic checks: 3/3 passed
   └─ Status: All valid
   │
   ▼
5. Output (0.05s)
   ├─ Status: "success"
   ├─ Total time: 4.15s
   ├─ API calls: 1
   └─ File: "output/id_1.json"
```

### Correction Flow Example

```
Extract → Validate → date_format_error
                          │
                          ▼
                    Correction Agent
                    (API Call #2, 1.5s)
                          │
                          ▼
                    Re-validate → Pass
                          │
                          ▼
                       Success
```

### Batch Processing Flow

```
Input: [id_1.jpg, id_2.jpg, ..., id_200.jpg]
   │
   ▼
Sequential Processing
   │
   ├─ id_1.jpg → Success (4s, 1 call)
   ├─ id_2.jpg → Success (3s, 1 call)
   ├─ id_3.jpg → Partial (5s, 2 calls)
   ├─ ...
   └─ id_200.jpg → Success (4s, 1 call)
   │
   ▼
Aggregation
   ├─ Total time: 780s (13 min)
   ├─ Successful: 185
   ├─ Needs review: 12
   ├─ Failed: 3
   ├─ Total API calls: 215
   └─ Estimated cost: $4.30
   │
   ▼
Output: batch_summary.json
```

## Agent Architecture

### Agent Communication Protocol

Agents communicate through structured data objects:

```python
# Extraction → Validation
extracted_data = {
    "surname": "SMITH",
    "given_names": "JOHN",
    ...
}

# Validation → Correction
validation_results = [
    ValidationResult(
        field_name="dob",
        is_valid=False,
        error_message="Invalid format"
    ),
    ...
]

# Correction → Pipeline
corrected_value = "13 Apr 1987"
```

### Agent Independence

Each agent is:
- **Stateless**: No persistent state between calls
- **Testable**: Can be tested in isolation
- **Replaceable**: Can swap implementations
- **Observable**: Logs all operations

### Agent Coordination

The `IDCardExtractionPipeline` class coordinates agents:

```python
def process_image(self, image_path):
    # 1. Preprocess
    processed_path = self.preprocessor.preprocess(image_path)
    
    # 2. Extract
    data = self.extraction_agent.extract(processed_path)
    
    # 3. Validate
    validations = self.validation_agent.validate_all(data)
    
    # 4. Correct if needed
    failed = [v for v in validations if not v.is_valid]
    for validation in failed:
        corrected = self.correction_agent.correct_field(
            processed_path, 
            validation.field_name,
            data[validation.field_name],
            validation.error_message
        )
        data[validation.field_name] = corrected
    
    # 5. Return result
    return ExtractionResult(fields=data, ...)
```

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.9+ | Main implementation |
| Vision API | OpenAI GPT-4V/4o | Latest | Field extraction |
| Image Processing | OpenCV | 4.8+ | Preprocessing |
| Image I/O | Pillow | 10.0+ | Image loading |
| Numerics | NumPy | 1.24+ | Array operations |
| Validation | Pydantic | 2.0+ | Schema validation |

### Supporting Libraries

- **logging**: Comprehensive logging
- **json**: Data serialization
- **re**: Regex validation
- **pathlib**: Path operations
- **argparse**: CLI interface
- **typing**: Type hints

### Development Tools

- **pytest**: Unit testing
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking

## Design Patterns

### 1. Agent Pattern
- Independent agents with single responsibilities
- Loose coupling through data objects
- Central orchestrator for coordination

### 2. Strategy Pattern
- Configurable preprocessing strategies
- Swappable validation rules
- Flexible correction strategies

### 3. Chain of Responsibility
- Sequential processing through pipeline stages
- Each stage can pass/fail/modify data
- Early termination on critical failures

### 4. Factory Pattern
- Agent instantiation
- Configuration object creation
- Result object construction

### 5. Retry Pattern
- Exponential backoff for API calls
- Configurable retry limits
- Graceful degradation

## Performance Considerations

### Time Complexity

| Operation | Complexity | Time | Notes |
|-----------|-----------|------|-------|
| Image Load | O(n) | 0.1-0.3s | n = pixels |
| Preprocessing | O(n) | 0.5-1.5s | Depends on filters |
| API Call | O(1) | 2-5s | Network + processing |
| Validation | O(1) | 0.05-0.1s | Pure Python |
| Total (no correction) | O(n) | 3-7s | Dominated by API |

### Space Complexity

- Image in memory: ~5-10 MB (2048x2048 RGB)
- Preprocessed image: ~5-10 MB
- API request: ~7-12 MB (base64 encoded)
- Total peak memory: ~20-30 MB per image

### Scalability

**Single Machine:**
- Sequential processing: ~450 images/hour
- Limited by API rate limits, not compute

**Distributed (Future):**
- Multiple workers with shared API quota
- Queue-based job distribution
- Estimated: 2000+ images/hour

### Bottlenecks

1. **OpenAI API latency** (2-5s per call)
   - Mitigation: Batch preprocessing, parallel requests
2. **Image preprocessing** (0.5-1.5s)
   - Mitigation: Optional disabling for clean images
3. **Rate limits** (60 requests/minute typical)
   - Mitigation: Built-in rate limiter

### Cost Optimization

- **Caching**: Save preprocessed images
- **Targeted Correction**: Only re-extract failed fields
- **Model Selection**: Use GPT-4o (cheaper) when possible
- **Batch Processing**: Amortize overhead costs

## Security Considerations

1. **API Key Protection**
   - Environment variables (not hardcoded)
   - .env file (gitignored)
   - No logging of API keys

2. **Input Validation**
   - File path sanitization
   - Image format verification
   - Size limits

3. **Output Sanitization**
   - No user input in file names
   - Safe JSON serialization
   - Path traversal prevention

## Monitoring and Observability

### Logging Levels

- **INFO**: Normal operations, status updates
- **WARNING**: Validation failures, retry attempts
- **ERROR**: API errors, processing failures
- **DEBUG**: Detailed trace information (optional)

### Metrics Tracked

- Processing time per image
- API calls per image
- Success/failure rates
- Validation failure patterns
- Cost per image

### Log Example

```
2025-01-26 10:30:45 - INFO - Processing image: id_1.jpg
2025-01-26 10:30:46 - INFO - Preprocessing: Corrected rotation 2.3°
2025-01-26 10:30:49 - INFO - ExtractionAgent: Successfully extracted fields
2025-01-26 10:30:49 - INFO - ValidationAgent: All validations passed
2025-01-26 10:30:49 - INFO - Pipeline completed: success (3.45s, 1 API call)
```

## Future Architecture Enhancements

1. **Caching Layer**: Redis for API response caching
2. **Queue System**: RabbitMQ/Celery for job distribution
3. **Database**: PostgreSQL for result persistence
4. **Monitoring**: Prometheus + Grafana for metrics
5. **API Gateway**: FastAPI for REST API interface
6. **Model Fine-tuning**: Custom model for Isaziland IDs

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Maintained By**: [Your Team]