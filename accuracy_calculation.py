#!/usr/bin/env python3
"""
Accuracy Calculator for ID Card Extraction Pipeline

This script compares extracted results with ground truth labels
and calculates field-level accuracy metrics.

Usage:
    python calculate_accuracy.py --results results/ --ground-truth isaziland_id_dataset/labels/
"""

import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class AccuracyCalculator:
    """Calculate accuracy metrics for ID card extraction"""
    
    def __init__(self):
        self.field_names = [
            'surname', 'given_names', 'id_number', 'dob',
            'gender', 'issue_date', 'expiry_date', 'issuing_authority'
        ]
        self.results = {
            'total_images': 0,
            'total_fields': 0,
            'correct_fields': 0,
            'per_field_correct': defaultdict(int),
            'per_field_total': defaultdict(int),
            'perfect_extractions': 0,
            'errors_by_field': defaultdict(list)
        }
    
    def normalize_value(self, value: str) -> str:
        """Normalize string for comparison (case-insensitive, strip whitespace)"""
        if not value:
            return ""
        return str(value).strip().upper()
    
    def compare_fields(self, predicted: Dict, ground_truth: Dict, image_name: str) -> Dict:
        """
        Compare predicted and ground truth fields
        
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'image': image_name,
            'total_fields': len(self.field_names),
            'correct_fields': 0,
            'field_results': {}
        }
        
        for field in self.field_names:
            pred_value = predicted.get(field, "")
            true_value = ground_truth.get(field, "")
            
            # Normalize for comparison (case-insensitive)
            pred_normalized = self.normalize_value(pred_value)
            true_normalized = self.normalize_value(true_value)
            
            is_correct = pred_normalized == true_normalized
            
            comparison['field_results'][field] = {
                'correct': is_correct,
                'predicted': pred_value,
                'ground_truth': true_value
            }
            
            if is_correct:
                comparison['correct_fields'] += 1
                self.results['per_field_correct'][field] += 1
            else:
                # Store error for analysis
                self.results['errors_by_field'][field].append({
                    'image': image_name,
                    'predicted': pred_value,
                    'ground_truth': true_value
                })
            
            self.results['per_field_total'][field] += 1
        
        return comparison
    
    def load_json_file(self, file_path: str) -> Dict:
        """Load JSON file safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {}
    
    def calculate_accuracy(self, results_dir: str, ground_truth_dir: str) -> Dict:
        """
        Calculate accuracy metrics
        
        Args:
            results_dir: Directory containing extraction results (JSON files)
            ground_truth_dir: Directory containing ground truth labels
        
        Returns:
            Dictionary with accuracy metrics
        """
        results_path = Path(results_dir)
        gt_path = Path(ground_truth_dir)
        
        if not results_path.exists():
            raise FileNotFoundError(f"Results directory not found: {results_dir}")
        
        if not gt_path.exists():
            raise FileNotFoundError(f"Ground truth directory not found: {ground_truth_dir}")
        
        # Get all result files
        result_files = list(results_path.glob("id_*.json"))
        
        if not result_files:
            raise ValueError(f"No result files (id_*.json) found in {results_dir}")
        
        print(f"\nFound {len(result_files)} result files")
        print(f"Comparing with ground truth in {ground_truth_dir}\n")
        
        comparisons = []
        missing_ground_truth = []
        
        for result_file in sorted(result_files):
            image_name = result_file.stem  # e.g., "id_1"
            gt_file = gt_path / f"{image_name}.json"
            
            if not gt_file.exists():
                missing_ground_truth.append(image_name)
                continue
            
            # Load both files
            predicted = self.load_json_file(str(result_file))
            ground_truth = self.load_json_file(str(gt_file))
            
            if not predicted or not ground_truth:
                continue
            
            # Compare
            comparison = self.compare_fields(predicted, ground_truth, image_name)
            comparisons.append(comparison)
            
            self.results['total_images'] += 1
            self.results['total_fields'] += comparison['total_fields']
            self.results['correct_fields'] += comparison['correct_fields']
            
            if comparison['correct_fields'] == comparison['total_fields']:
                self.results['perfect_extractions'] += 1
        
        if missing_ground_truth:
            print(f"Warning: {len(missing_ground_truth)} files missing ground truth labels")
        
        return self.generate_report(comparisons)
    
    def generate_report(self, comparisons: List[Dict]) -> Dict:
        """Generate detailed accuracy report"""
        
        if self.results['total_fields'] == 0:
            return {'error': 'No valid comparisons made'}
        
        # Calculate overall accuracy
        field_level_accuracy = (self.results['correct_fields'] / 
                                self.results['total_fields'] * 100)
        
        image_level_accuracy = (self.results['perfect_extractions'] / 
                                self.results['total_images'] * 100)
        
        # Calculate per-field accuracy
        per_field_accuracy = {}
        for field in self.field_names:
            correct = self.results['per_field_correct'][field]
            total = self.results['per_field_total'][field]
            accuracy = (correct / total * 100) if total > 0 else 0
            per_field_accuracy[field] = {
                'correct': correct,
                'total': total,
                'accuracy': round(accuracy, 2)
            }
        
        # Generate report
        report = {
            'summary': {
                'total_images': self.results['total_images'],
                'total_fields': self.results['total_fields'],
                'correct_fields': self.results['correct_fields'],
                'incorrect_fields': self.results['total_fields'] - self.results['correct_fields'],
                'field_level_accuracy': round(field_level_accuracy, 2),
                'image_level_accuracy': round(image_level_accuracy, 2),
                'perfect_extractions': self.results['perfect_extractions']
            },
            'per_field_accuracy': per_field_accuracy,
            'error_analysis': self.generate_error_analysis(),
            'detailed_results': comparisons
        }
        
        return report
    
    def generate_error_analysis(self) -> Dict:
        """Generate error analysis by field"""
        error_analysis = {}
        
        for field, errors in self.results['errors_by_field'].items():
            if not errors:
                continue
            
            error_analysis[field] = {
                'total_errors': len(errors),
                'error_rate': round(len(errors) / self.results['per_field_total'][field] * 100, 2),
                'sample_errors': errors[:5]  # First 5 errors as examples
            }
        
        return error_analysis
    
    def print_report(self, report: Dict):
        """Print formatted accuracy report"""
        
        print("\n" + "="*70)
        print("ACCURACY REPORT")
        print("="*70 + "\n")
        
        # Summary
        summary = report['summary']
        print("OVERALL METRICS:")
        print("-" * 70)
        print(f"Total Images Processed:        {summary['total_images']}")
        print(f"Total Fields:                  {summary['total_fields']}")
        print(f"Correct Fields:                {summary['correct_fields']}")
        print(f"Incorrect Fields:              {summary['incorrect_fields']}")
        print(f"\n{'FIELD-LEVEL ACCURACY:':<30} {summary['field_level_accuracy']:.2f}%")
        print(f"{'IMAGE-LEVEL ACCURACY:':<30} {summary['image_level_accuracy']:.2f}%")
        print(f"Perfect Extractions:           {summary['perfect_extractions']}/{summary['total_images']}")
        
        # Per-field accuracy
        print("\n\nPER-FIELD ACCURACY:")
        print("-" * 70)
        print(f"{'Field':<25} {'Correct':<10} {'Total':<10} {'Accuracy':<10}")
        print("-" * 70)
        
        for field in self.field_names:
            stats = report['per_field_accuracy'][field]
            print(f"{field:<25} {stats['correct']:<10} {stats['total']:<10} {stats['accuracy']:.2f}%")
        
        # Error analysis
        if report['error_analysis']:
            print("\n\nERROR ANALYSIS (Top Issues):")
            print("-" * 70)
            
            # Sort fields by error count
            sorted_errors = sorted(
                report['error_analysis'].items(),
                key=lambda x: x[1]['total_errors'],
                reverse=True
            )
            
            for field, error_info in sorted_errors[:5]:  # Top 5 problematic fields
                print(f"\n{field.upper()} - {error_info['total_errors']} errors ({error_info['error_rate']:.1f}%)")
                
                if error_info['sample_errors']:
                    print("  Sample errors:")
                    for i, err in enumerate(error_info['sample_errors'][:3], 1):
                        print(f"    {i}. Image: {err['image']}")
                        print(f"       Predicted:    '{err['predicted']}'")
                        print(f"       Ground Truth: '{err['ground_truth']}'")
        
        print("\n" + "="*70 + "\n")
    
    def save_report(self, report: Dict, output_file: str):
        """Save report to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Detailed report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Calculate accuracy metrics for ID card extraction'
    )
    parser.add_argument(
        '--results',
        default='results',
        help='Directory containing extraction results (default: results)'
    )
    parser.add_argument(
        '--ground-truth',
        default='isaziland_id_dataset/labels',
        help='Directory containing ground truth labels (default: isaziland_id_dataset/labels)'
    )
    parser.add_argument(
        '--output',
        default='accuracy_report.json',
        help='Output file for detailed report (default: accuracy_report.json)'
    )
    
    args = parser.parse_args()
    
    # Calculate accuracy
    calculator = AccuracyCalculator()
    
    try:
        report = calculator.calculate_accuracy(args.results, args.ground_truth)
        
        # Print report to console
        calculator.print_report(report)
        
        # Save detailed report
        calculator.save_report(report, args.output)
        
        # Print summary for easy reference
        print("\nQUICK SUMMARY:")
        print(f"  Field-Level Accuracy: {report['summary']['field_level_accuracy']:.2f}%")
        print(f"  Image-Level Accuracy: {report['summary']['image_level_accuracy']:.2f}%")
        print(f"  Perfect Extractions:  {report['summary']['perfect_extractions']}/{report['summary']['total_images']}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())