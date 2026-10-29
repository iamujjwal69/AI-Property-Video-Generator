"""
Unit tests for validators, script generator, and pipeline components.
"""

from pathlib import Path
import pytest
from src.script_generator import generate_property_script
from src.validators import validate_property_data, validate_single_image


@pytest.fixture
def sample_property():
    return {
        "property_name": "Sunrise Residency",
        "location": "Whitefield, Bengaluru",
        "price": "INR 85,00,000",
        "property_type": "3 BHK Apartment",
        "key_features": "Covered parking, 24x7 security, children's play area, clubhouse",
        "contact_info": "Call 98765 43210 to schedule a site visit",
    }


def test_validation_success(sample_property):
    # Mock 5 valid images (using sample_images if present)
    sample_imgs_dir = Path(__file__).resolve().parent.parent / "sample_images"
    imgs = sorted(list(sample_imgs_dir.glob("*.jpg")))
    assert len(imgs) >= 4, "Sample images must exist"

    is_valid, errors = validate_property_data(sample_property, imgs)
    assert is_valid is True
    assert len(errors) == 0


def test_validation_missing_name(sample_property):
    sample_imgs_dir = Path(__file__).resolve().parent.parent / "sample_images"
    imgs = sorted(list(sample_imgs_dir.glob("*.jpg")))

    bad_data = sample_property.copy()
    bad_data["property_name"] = "   "

    is_valid, errors = validate_property_data(bad_data, imgs)
    assert is_valid is False
    assert any("Property Name" in e for e in errors)


def test_validation_invalid_price(sample_property):
    sample_imgs_dir = Path(__file__).resolve().parent.parent / "sample_images"
    imgs = sorted(list(sample_imgs_dir.glob("*.jpg")))

    bad_data = sample_property.copy()
    bad_data["price"] = "abc"

    is_valid, errors = validate_property_data(bad_data, imgs)
    assert is_valid is False
    assert any("Price format" in e for e in errors)


def test_validation_fewer_than_4_images(sample_property):
    sample_imgs_dir = Path(__file__).resolve().parent.parent / "sample_images"
    imgs = sorted(list(sample_imgs_dir.glob("*.jpg")))[:3]

    is_valid, errors = validate_property_data(sample_property, imgs)
    assert is_valid is False
    assert any("At least 4 images" in e for e in errors)


def test_validation_more_than_8_images(sample_property):
    sample_imgs_dir = Path(__file__).resolve().parent.parent / "sample_images"
    imgs = sorted(list(sample_imgs_dir.glob("*.jpg"))) * 2  # 10 images

    is_valid, errors = validate_property_data(sample_property, imgs)
    assert is_valid is False
    assert any("Maximum 8 images" in e for e in errors)


def test_script_generator_durations(sample_property):
    for n in range(4, 9):
        script = generate_property_script(sample_property, image_count=n)
        assert len(script["captions"]) == n
        assert len(script["durations"]) == n + 2
        total_d = sum(script["durations"])
        assert 20.0 <= total_d <= 30.0, f"Duration {total_d} out of 20-30s range for n={n}"
        assert sample_property["property_name"] in script["title"]
        assert sample_property["price"] in script["price_line"]
        assert sample_property["contact_info"] in script["closing"]
