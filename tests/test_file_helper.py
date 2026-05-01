
import pytest
from pathlib import Path
from jpio.utils.file_helper import detect_existing_folders
from jpio.core.models import FolderMapping

def test_detect_existing_folders_default(tmp_path):
    # Empty folder -> default mapping
    mapping = detect_existing_folders(tmp_path)
    assert mapping.entity == "models/entity"
    assert mapping.controller == "controller"

def test_detect_existing_folders_custom(tmp_path):
    # Create folders with synonyms
    (tmp_path / "web").mkdir()
    (tmp_path / "services").mkdir()
    (tmp_path / "model").mkdir()
    (tmp_path / "repo").mkdir()
    
    mapping = detect_existing_folders(tmp_path)
    assert mapping.controller == "web"
    assert mapping.service == "services"
    assert mapping.entity == "model"
    assert mapping.repository == "repo"

def test_detect_existing_folders_nested_models(tmp_path):
    # Create models/entity
    (tmp_path / "models" / "entity").mkdir(parents=True)
    
    mapping = detect_existing_folders(tmp_path)
    assert mapping.entity == "models/entity"

def test_detect_existing_folders_nested_models_model(tmp_path):
    # Create models/model
    (tmp_path / "models" / "model").mkdir(parents=True)
    
    mapping = detect_existing_folders(tmp_path)
    assert mapping.entity == "models/model"
