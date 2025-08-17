"""
Test configuration loading and validation
"""
import pytest
import tempfile
import yaml
from pathlib import Path
from src.config import load_config, BoardConfig


class TestConfigLoading:
    """Test configuration loading from YAML files"""
    
    def test_load_valid_config(self):
        """Test loading a valid configuration"""
        config_data = {
            "product": {
                "name": "Test Product",
                "description": "A test product for validation"
            },
            "hypotheses": [
                {"id": "H1", "description": "Users want simplicity"},
                {"id": "H2", "description": "Price is a key factor"}
            ],
            "questions": {},
            "personas": [
                {
                    "id": "p1",
                    "name": "Sarah",
                    "background": "Tech-savvy professional, 30s"
                },
                {
                    "id": "p2", 
                    "name": "Mike",
                    "background": "Budget-conscious student, 20s"
                }
            ]
        }
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            
            # Test product
            assert config.product.name == "Test Product"
            assert config.product.description == "A test product for validation"
            
            # Test hypotheses
            assert len(config.hypotheses) == 2
            assert config.hypotheses[0].id == "H1"
            assert config.hypotheses[1].id == "H2"
            
            # Test personas
            assert len(config.personas) == 2
            assert config.personas[0].name == "Sarah"
            assert config.personas[1].name == "Mike"
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_config_with_questions(self):
        """Test loading config with phase questions"""
        config_data = {
            "product": {
                "name": "Test Product",
                "description": "Test"
            },
            "hypotheses": [
                {"id": "H1", "description": "Test hypothesis"}
            ],
            "personas": [
                {"id": "p1", "name": "Test", "background": "Test background"}
            ],
            "questions": {
                "warmup": ["What are your first impressions?"],
                "diverge": [
                    {"text": "What features matter most?", "covers": ["H1"]},
                    "What concerns do you have?"
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            
            # Test questions structure
            assert hasattr(config, 'questions')
            assert hasattr(config.questions, 'warmup')
            assert hasattr(config.questions, 'diverge')
            
            # Test warmup questions
            assert len(config.questions.warmup) == 1
            assert config.questions.warmup[0] == "What are your first impressions?"
            
            # Test diverge questions (mixed format)
            assert len(config.questions.diverge) == 2
            
        finally:
            Path(temp_path).unlink()
    
    def test_load_config_missing_file(self):
        """Test loading non-existent config file"""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent_file.yml")
    
    def test_load_config_invalid_yaml(self):
        """Test loading invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            with pytest.raises(yaml.YAMLError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_load_config_missing_required_fields(self):
        """Test loading config with missing required fields"""
        config_data = {
            "product": {
                "name": "Test Product"
                # Missing description
            }
            # Missing hypotheses and personas
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()


class TestBoardConfig:
    """Test BoardConfig model functionality"""
    
    def test_get_hypothesis_ids(self):
        """Test getting hypothesis IDs"""
        config_data = {
            "product": {"name": "Test", "description": "Test"},
            "hypotheses": [
                {"id": "H1", "description": "Test 1"},
                {"id": "H2", "description": "Test 2"},
                {"id": "H3", "description": "Test 3"}
            ],
            "questions": {},
            "personas": [
                {"id": "p1", "name": "Test", "background": "Test"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            hypothesis_ids = config.get_hypothesis_ids()
            
            assert hypothesis_ids == ["H1", "H2", "H3"]
            assert len(hypothesis_ids) == 3
            
        finally:
            Path(temp_path).unlink()
    
    def test_get_persona_ids(self):
        """Test getting persona IDs"""
        config_data = {
            "product": {"name": "Test", "description": "Test"},
            "hypotheses": [
                {"id": "H1", "description": "Test"}
            ],
            "questions": {},
            "personas": [
                {"id": "p1", "name": "Sarah", "background": "Test 1"},
                {"id": "p2", "name": "Mike", "background": "Test 2"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            persona_ids = [p.id for p in config.personas]
            
            assert persona_ids == ["p1", "p2"]
            assert len(persona_ids) == 2
            
        finally:
            Path(temp_path).unlink()
    
    def test_config_validation_empty_hypotheses(self):
        """Test that empty hypotheses list is allowed (config loads successfully)"""
        config_data = {
            "product": {"name": "Test", "description": "Test"},
            "hypotheses": [],  # Empty list is now allowed
            "questions": {},
            "personas": [
                {"id": "p1", "name": "Test", "background": "Test"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            assert len(config.hypotheses) == 0
            assert len(config.personas) == 1
        finally:
            Path(temp_path).unlink()
    
    def test_config_validation_empty_personas(self):
        """Test that empty personas list is allowed (config loads successfully)"""
        config_data = {
            "product": {"name": "Test", "description": "Test"},
            "hypotheses": [
                {"id": "H1", "description": "Test"}
            ],
            "questions": {},
            "personas": []  # Empty list is now allowed
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            assert len(config.hypotheses) == 1
            assert len(config.personas) == 0
        finally:
            Path(temp_path).unlink()