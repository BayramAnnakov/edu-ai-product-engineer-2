import json
import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.feedback import FeedbackItem


class FileProcessor:
    """Processor for reading feedback from various file formats."""
    
    SUPPORTED_FORMATS = {'.txt', '.csv', '.json', '.xlsx'}
    
    def __init__(self):
        pass
    
    def process_file(self, file_path: str) -> List[FeedbackItem]:
        """Process a file and return a list of FeedbackItem objects."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        if path.suffix.lower() == '.txt':
            return self._process_txt(path)
        elif path.suffix.lower() == '.csv':
            return self._process_csv(path)
        elif path.suffix.lower() == '.json':
            return self._process_json(path)
        elif path.suffix.lower() == '.xlsx':
            return self._process_xlsx(path)
    
    def _process_txt(self, path: Path) -> List[FeedbackItem]:
        """Process plain text file - each line is a separate feedback item."""
        feedback_items = []
        
        with open(path, 'r', encoding='utf-8') as file:
            for i, line in enumerate(file, 1):
                line = line.strip()
                if line:  # Skip empty lines
                    item = FeedbackItem(
                        id=f"{path.stem}_{i}",
                        text=line,
                        source=str(path),
                        timestamp=datetime.now(),
                        metadata={"line_number": i}
                    )
                    feedback_items.append(item)
        
        return feedback_items
    
    def _process_csv(self, path: Path) -> List[FeedbackItem]:
        """Process CSV file with feedback data."""
        feedback_items = []
        
        try:
            df = pd.read_csv(path)
            
            # Try to detect common column names
            text_column = self._find_text_column(df.columns)
            if not text_column:
                raise ValueError("Could not find feedback text column in CSV")
            
            for index, row in df.iterrows():
                # Extract basic fields
                text = str(row[text_column]).strip()
                if not text or text.lower() in ['nan', 'none', '']:
                    continue
                
                # Try to extract other common fields
                timestamp = self._extract_timestamp(row)
                user_id = self._extract_user_id(row)
                
                # Create metadata from remaining columns
                metadata = {}
                for col in df.columns:
                    if col != text_column and pd.notna(row[col]):
                        metadata[col] = row[col]
                
                item = FeedbackItem(
                    id=f"{path.stem}_{index}",
                    text=text,
                    source=str(path),
                    timestamp=timestamp,
                    user_id=user_id,
                    metadata=metadata
                )
                feedback_items.append(item)
                
        except Exception as e:
            raise ValueError(f"Error processing CSV file: {e}")
        
        return feedback_items
    
    def _process_json(self, path: Path) -> List[FeedbackItem]:
        """Process JSON file with feedback data."""
        feedback_items = []
        
        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of feedback objects
                for i, item in enumerate(data):
                    feedback_item = self._parse_json_feedback_item(item, path, i)
                    if feedback_item:
                        feedback_items.append(feedback_item)
            elif isinstance(data, dict):
                if 'feedback' in data and isinstance(data['feedback'], list):
                    # Object with feedback array
                    for i, item in enumerate(data['feedback']):
                        feedback_item = self._parse_json_feedback_item(item, path, i)
                        if feedback_item:
                            feedback_items.append(feedback_item)
                else:
                    # Single feedback object
                    feedback_item = self._parse_json_feedback_item(data, path, 0)
                    if feedback_item:
                        feedback_items.append(feedback_item)
                        
        except Exception as e:
            raise ValueError(f"Error processing JSON file: {e}")
        
        return feedback_items
    
    def _process_xlsx(self, path: Path) -> List[FeedbackItem]:
        """Process Excel file with feedback data."""
        try:
            df = pd.read_excel(path)
            # Convert to CSV-like processing
            return self._process_dataframe(df, path)
        except Exception as e:
            raise ValueError(f"Error processing Excel file: {e}")
    
    def _process_dataframe(self, df: pd.DataFrame, path: Path) -> List[FeedbackItem]:
        """Helper method to process pandas DataFrame."""
        feedback_items = []
        
        text_column = self._find_text_column(df.columns)
        if not text_column:
            raise ValueError("Could not find feedback text column")
        
        for index, row in df.iterrows():
            text = str(row[text_column]).strip()
            if not text or text.lower() in ['nan', 'none', '']:
                continue
            
            timestamp = self._extract_timestamp(row)
            user_id = self._extract_user_id(row)
            
            metadata = {}
            for col in df.columns:
                if col != text_column and pd.notna(row[col]):
                    metadata[col] = row[col]
            
            item = FeedbackItem(
                id=f"{path.stem}_{index}",
                text=text,
                source=str(path),
                timestamp=timestamp,
                user_id=user_id,
                metadata=metadata
            )
            feedback_items.append(item)
        
        return feedback_items
    
    def _find_text_column(self, columns) -> Optional[str]:
        """Find the column that likely contains feedback text."""
        text_keywords = ['feedback', 'comment', 'text', 'message', 'review', 'description', 
                        'коммент', 'комментарий', 'отзыв', 'сообщение', 'текст', 'описание']
        
        columns_lower = [col.lower() for col in columns]
        
        # Direct match
        for keyword in text_keywords:
            if keyword in columns_lower:
                return columns[columns_lower.index(keyword)]
        
        # Partial match
        for keyword in text_keywords:
            for i, col in enumerate(columns_lower):
                if keyword in col:
                    return columns[i]
        
        # Fallback to first text-like column
        for col in columns:
            if any(keyword in col.lower() for keyword in ['text', 'comment', 'feedback']):
                return col
        
        return None
    
    def _extract_timestamp(self, row) -> Optional[datetime]:
        """Extract timestamp from row data."""
        timestamp_keywords = ['timestamp', 'date', 'created_at', 'time', 'submitted_at']
        
        for keyword in timestamp_keywords:
            for col_name in row.index:
                if keyword in col_name.lower() and pd.notna(row[col_name]):
                    try:
                        return pd.to_datetime(row[col_name])
                    except:
                        continue
        
        return None
    
    def _extract_user_id(self, row) -> Optional[str]:
        """Extract user ID from row data."""
        user_keywords = ['user_id', 'userid', 'user', 'customer_id', 'id']
        
        for keyword in user_keywords:
            for col_name in row.index:
                if keyword in col_name.lower() and pd.notna(row[col_name]):
                    return str(row[col_name])
        
        return None
    
    def _parse_json_feedback_item(self, item: Dict[str, Any], path: Path, index: int) -> Optional[FeedbackItem]:
        """Parse a single feedback item from JSON data."""
        if isinstance(item, str):
            return FeedbackItem(
                id=f"{path.stem}_{index}",
                text=item,
                source=str(path),
                timestamp=datetime.now()
            )
        
        if not isinstance(item, dict):
            return None
        
        # Find text field
        text = None
        text_fields = ['text', 'feedback', 'comment', 'message', 'review', 'description']
        for field in text_fields:
            if field in item and item[field]:
                text = str(item[field]).strip()
                break
        
        if not text:
            return None
        
        # Extract other fields
        timestamp = None
        if 'timestamp' in item:
            try:
                timestamp = pd.to_datetime(item['timestamp'])
            except:
                pass
        
        user_id = item.get('user_id') or item.get('userId') or item.get('user')
        if user_id:
            user_id = str(user_id)
        
        # Create metadata from remaining fields
        metadata = {}
        excluded_fields = {'text', 'feedback', 'comment', 'message', 'review', 'description', 'timestamp', 'user_id', 'userId', 'user'}
        for key, value in item.items():
            if key not in excluded_fields and value is not None:
                metadata[key] = value
        
        return FeedbackItem(
            id=item.get('id', f"{path.stem}_{index}"),
            text=text,
            source=str(path),
            timestamp=timestamp,
            user_id=user_id,
            metadata=metadata
        )