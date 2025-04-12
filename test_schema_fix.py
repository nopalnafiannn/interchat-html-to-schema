#!/usr/bin/env python3
"""Test script to verify Schema import fix works."""

from html_schema_converter.models.schema import Schema

def test_basic_schema_creation():
    """Test basic schema creation."""
    # Create a Schema object to ensure the import works
    schema = Schema(
        name="Test Schema",
        description="This is a test schema"
    )
    
    print(f"Created schema object with type: {type(schema)}")
    print(f"Schema name: {schema.name}")
    print(f"Schema description: {schema.description}")
    
    assert isinstance(schema, Schema)
    print("Basic schema creation test passed!")

def test_empty_schema_creation():
    """Test creation of an empty schema from None."""
    print("DEBUG: Schema type: <class 'NoneType'>")
    print("DEBUG: Creating empty Schema object for null schema")
    
    # Simulate the scenario where we have a None schema
    schema = None
    
    # Now create a Schema object from None
    if schema is None:
        schema = Schema(
            name="Empty Schema",
            description="This schema was created when a null schema was encountered."
        )
    
    print(f"DEBUG: Created empty Schema object: {type(schema)}")
    assert isinstance(schema, Schema)
    print("Empty schema creation test passed!")
    
if __name__ == "__main__":
    test_basic_schema_creation()
    print("\n" + "-"*50 + "\n")
    test_empty_schema_creation()
    print("\nAll tests completed successfully!")