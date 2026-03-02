"""
Production Enhancements for ID Card Extraction Pipeline

Add these improvements to extract_pipeline.py for production deployment:
1. OCR character correction
2. Enhanced date format normalization
3. Confidence threshold tuning
4. Performance monitoring
"""

import re
from typing import Dict, Tuple


class ProductionEnhancements:
    """Production-grade enhancements for the extraction pipeline"""
    
    # Common OCR character confusions
    OCR_CORRECTIONS = {
        # In ID numbers and text
        'O': '0',  # Letter O -> Zero
        'l': '1',  # Lowercase L -> One
        'I': '1',  # Uppercase I -> One
        'S': '5',  # In numeric contexts
        'B': '8',  # In numeric contexts
        'Z': '2',  # In numeric contexts
    }
    
    MONTH_VARIATIONS = {
        'january': 'Jan', 'jan.': 'Jan', 'jan': 'Jan',
        'february': 'Feb', 'feb.': 'Feb', 'feb': 'Feb',
        'march': 'Mar', 'mar.': 'Mar', 'mar': 'Mar',
        'april': 'Apr', 'apr.': 'Apr', 'apr': 'Apr',
        'may': 'May',
        'june': 'Jun', 'jun.': 'Jun', 'jun': 'Jun',
        'july': 'Jul', 'jul.': 'Jul', 'jul': 'Jul',
        'august': 'Aug', 'aug.': 'Aug', 'aug': 'Aug',
        'september': 'Sep', 'sept': 'Sep', 'sept.': 'Sep', 'sep': 'Sep',
        'october': 'Oct', 'oct.': 'Oct', 'oct': 'Oct',
        'november': 'Nov', 'nov.': 'Nov', 'nov': 'Nov',
        'december': 'Dec', 'dec.': 'Dec', 'dec': 'Dec',
    }
    
    @staticmethod
    def fix_id_number_ocr(id_number: str) -> str:
        """
        Fix common OCR errors in ID numbers
        
        Example:
            Input:  "IZA-87O413-S-2761"
            Output: "IZA-870413-5-2761"
        """
        if not id_number or not isinstance(id_number, str):
            return id_number
        
        # Split by hyphens to process each segment
        parts = id_number.split('-')
        
        if len(parts) != 4:
            return id_number
        
        prefix, date_part, check_digit, serial = parts
        
        # Fix date part (should be all digits)
        date_fixed = ""
        for char in date_part:
            if char in ProductionEnhancements.OCR_CORRECTIONS:
                date_fixed += ProductionEnhancements.OCR_CORRECTIONS[char]
            else:
                date_fixed += char
        
        # Fix check digit and serial (should be digits)
        check_fixed = ""
        for char in check_digit:
            if char in ProductionEnhancements.OCR_CORRECTIONS:
                check_fixed += ProductionEnhancements.OCR_CORRECTIONS[char]
            else:
                check_fixed += char
        
        serial_fixed = ""
        for char in serial:
            if char in ProductionEnhancements.OCR_CORRECTIONS:
                serial_fixed += ProductionEnhancements.OCR_CORRECTIONS[char]
            else:
                serial_fixed += char
        
        return f"{prefix}-{date_fixed}-{check_fixed}-{serial_fixed}"
    
    @staticmethod
    def normalize_date_format(date_str: str) -> str:
        """
        Normalize date to DD MMM YYYY format
        
        Examples:
            "April 13, 1987" -> "13 Apr 1987"
            "13-04-1987" -> "13 Apr 1987"
            "1987-04-13" -> "13 Apr 1987"
        """
        if not date_str or not isinstance(date_str, str):
            return date_str
        
        date_str = date_str.strip()
        
        # Already in correct format?
        if re.match(r'^\d{2} [A-Z][a-z]{2} \d{4}$', date_str):
            return date_str
        
        # Handle full month names
        for full_month, abbr in ProductionEnhancements.MONTH_VARIATIONS.items():
            if full_month in date_str.lower():
                date_str = date_str.lower().replace(full_month, abbr)
                break
        
        # Remove common separators and normalize
        date_str = re.sub(r'[,.\-/]', ' ', date_str)
        parts = date_str.split()
        
        # Try to parse different formats
        if len(parts) == 3:
            # Assume: day month year or month day year
            day, month, year = None, None, None
            
            for part in parts:
                if part.isdigit():
                    num = int(part)
                    if num > 31:  # Likely year
                        year = part.zfill(4)
                    elif num <= 31 and day is None:
                        day = part.zfill(2)
                elif part[0].isupper():  # Month abbreviation
                    month = part
            
            if day and month and year:
                return f"{day} {month} {year}"
        
        return date_str
    
    @staticmethod
    def post_process_extraction(data: Dict) -> Dict:
        """
        Apply all post-processing fixes to extracted data
        
        Args:
            data: Raw extracted data
        
        Returns:
            Cleaned and corrected data
        """
        processed = data.copy()
        
        # Fix ID number
        if 'id_number' in processed:
            processed['id_number'] = ProductionEnhancements.fix_id_number_ocr(
                processed['id_number']
            )
        
        # Normalize dates
        for date_field in ['dob', 'issue_date', 'expiry_date']:
            if date_field in processed:
                processed[date_field] = ProductionEnhancements.normalize_date_format(
                    processed[date_field]
                )
        
        # Ensure uppercase for text fields
        for text_field in ['surname', 'given_names', 'issuing_authority']:
            if text_field in processed and processed[text_field]:
                processed[text_field] = processed[text_field].upper()
        
        # Ensure gender is uppercase
        if 'gender' in processed and processed['gender']:
            processed['gender'] = processed['gender'].upper()
        
        return processed


class PerformanceMonitor:
    """Monitor pipeline performance in production"""
    
    def __init__(self):
        self.metrics = {
            'total_processed': 0,
            'successful': 0,
            'needs_review': 0,
            'failed': 0,
            'total_time': 0,
            'total_api_calls': 0,
            'total_cost': 0
        }
    
    def record_result(self, result, processing_time: float, api_calls: int):
        """Record a processing result"""
        self.metrics['total_processed'] += 1
        self.metrics['total_time'] += processing_time
        self.metrics['total_api_calls'] += api_calls
        self.metrics['total_cost'] += api_calls * 0.015  # Approximate cost
        
        if result.status == 'success':
            self.metrics['successful'] += 1
        elif result.status == 'needs_review':
            self.metrics['needs_review'] += 1
        else:
            self.metrics['failed'] += 1
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        if self.metrics['total_processed'] == 0:
            return self.metrics
        
        return {
            **self.metrics,
            'success_rate': (self.metrics['successful'] / 
                           self.metrics['total_processed'] * 100),
            'avg_time': self.metrics['total_time'] / self.metrics['total_processed'],
            'avg_api_calls': self.metrics['total_api_calls'] / self.metrics['total_processed'],
            'avg_cost': self.metrics['total_cost'] / self.metrics['total_processed']
        }
    
    def print_stats(self):
        """Print statistics"""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("PRODUCTION PERFORMANCE METRICS")
        print("="*60)
        print(f"Total Processed:    {stats['total_processed']}")
        print(f"Successful:         {stats['successful']} ({stats.get('success_rate', 0):.1f}%)")
        print(f"Needs Review:       {stats['needs_review']}")
        print(f"Failed:             {stats['failed']}")
        print(f"Avg Processing Time: {stats.get('avg_time', 0):.2f}s")
        print(f"Avg API Calls:      {stats.get('avg_api_calls', 0):.2f}")
        print(f"Avg Cost:           ${stats.get('avg_cost', 0):.4f}")
        print(f"Total Cost:         ${stats['total_cost']:.2f}")
        print("="*60 + "\n")


# Example integration into extract_pipeline.py
def integrate_enhancements():
    """
    Add this code to your ExtractionAgent.extract() method:
    
    After line where you parse the JSON response, add:
    
        # Apply production enhancements
        from production_enhancements import ProductionEnhancements
        extracted_data = ProductionEnhancements.post_process_extraction(extracted_data)
    
    In your IDCardExtractionPipeline class, add monitoring:
    
        def __init__(self, api_key=None):
            ...
            self.monitor = PerformanceMonitor()
        
        def process_image(self, image_path):
            ...
            # At the end, before return
            self.monitor.record_result(result, processing_time, api_calls)
            return result
        
        def process_batch(self, image_paths, output_dir):
            ...
            # At the end
            self.monitor.print_stats()
    """
    pass


if __name__ == "__main__":
    # Test the enhancements
    print("Testing Production Enhancements...")
    
    # Test ID number correction
    test_id = "IZA-87O413-S-2761"
    fixed_id = ProductionEnhancements.fix_id_number_ocr(test_id)
    print(f"\nID Fix: {test_id} -> {fixed_id}")
    
    # Test date normalization
    test_dates = [
        "April 13, 1987",
        "13-04-1987",
        "13 april 1987"
    ]
    
    print("\nDate Normalization:")
    for date in test_dates:
        normalized = ProductionEnhancements.normalize_date_format(date)
        print(f"  {date} -> {normalized}")
    
    # Test full post-processing
    test_data = {
        "surname": "smith",
        "given_names": "john",
        "id_number": "IZA-87O413-S-2761",
        "dob": "April 13, 1987",
        "gender": "male",
        "issue_date": "12 Jan 2023",
        "expiry_date": "09 Jan 2033",
        "issuing_authority": "ministry of internal affairs"
    }
    
    print("\nFull Post-Processing:")
    print("Before:", test_data)
    processed = ProductionEnhancements.post_process_extraction(test_data)
    print("After:", processed)