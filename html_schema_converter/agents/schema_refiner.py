# html_schema_converter/agents/schema_refiner.py
from typing import Dict, Any
from html_schema_converter.llm.openai_client import OpenAIClient
from html_schema_converter.config import config
from html_schema_converter.utils.metrics import track_metrics
from html_schema_converter.models.schema import Schema

class SchemaRefiner:
    """Agent for refining data schemas based on human feedback."""
    
    def __init__(self):
        """Initialize the schema refiner with LLM client."""
        self.llm_client = OpenAIClient()
        self.model = config.get("llm.schema_refinement_model", "gpt-3.5-turbo-16k")
        self.temperature = config.get("llm.temperature", 0)
        self.max_tokens = config.get("schema_refinement.max_tokens", 2000)
    
    @track_metrics
    def refine_schema(self, original_schema: Schema, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine the generated schema by incorporating human feedback.
        
        Args:
            original_schema: Original Schema object
            feedback: Dictionary with user feedback
            
        Returns:
            Dictionary with updated schema and metrics
        """
        # Convert schema to JSON string for the prompt
        original_json = original_schema.to_json()
        
        # Create a refined prompt that emphasizes precision in data types
        refined_prompt = f"""
        You are tasked with refining a data schema based on user feedback. 
        
        Original schema:
        {original_json}
        
        User feedback:
        {feedback}
        
        Please refine the schema to incorporate the user's feedback. Pay special attention to:
        
        1. Use precise Python data types (int, float, str, list, tuple, dict, bool, bytes, NoneType, etc.)
        2. Add appropriate format specifications for dates, times, and special string formats
        3. Include constraints like minimum/maximum values or regex patterns when relevant
        4. Maintain the overall structure and naming of the original schema
        
        Generate valid JSON that can be parsed directly. Return ONLY the updated schema JSON.
        """
        
        # Generate updated schema using LLM
        response = self.llm_client.generate(
            prompt=refined_prompt,
            model=self.model,
            system_message="You are a data schema refinement engine that specializes in precise type definitions and data validation rules. Output only valid JSON without markdown code blocks (```). Return only the JSON object with no additional text.",
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        schema_text = response["content"].strip()
        
        # Parse the schema text to create a new Schema object
        try:
            # Clean up the text before parsing
            cleaned_text = schema_text.strip()
            
            # Remove markdown code block markers if present
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # Try to extract valid JSON if there's text around it
            try:
                # Check if direct parsing works
                updated_schema = Schema.from_json(cleaned_text)
            except:
                # Try to find valid JSON within the text
                start_idx = cleaned_text.find("{")
                end_idx = cleaned_text.rfind("}")
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    extracted_json = cleaned_text[start_idx:end_idx+1]
                    updated_schema = Schema.from_json(extracted_json)
                else:
                    raise ValueError("Could not extract valid JSON from LLM response")
            
            # Preserve metadata from original schema
            updated_schema.metadata = original_schema.metadata.copy()
            updated_schema.metadata['feedback_incorporated'] = True
            updated_schema.metadata['refinement_version'] = original_schema.metadata.get('refinement_version', 0) + 1
            
            return {
                "schema": updated_schema,
                "raw_output": cleaned_text,
                "metrics": response.get("metrics", {})
            }
        except Exception as e:
            return {
                "schema": original_schema,
                "error": f"Failed to parse refined schema: {str(e)}",
                "raw_output": schema_text,
                "metrics": response.get("metrics", {})
            }

# Maintain backward compatibility with simple function version
def refine_schema(original_schema: str, feedback: str) -> str:
    """
    Legacy function for schema refinement to maintain backwards compatibility.
    
    Args:
        original_schema: The original schema as a string (JSON or YAML)
        feedback: User feedback text
        
    Returns:
        Refined schema as a string in the same format as the input
    """
    refiner = SchemaRefiner()
    
    # Convert string to Schema object
    try:
        schema_obj = Schema.from_json(original_schema)
    except:
        # If parsing fails, use a simplified approach
        refined_prompt = (
            "Below is the original data schema generated for the HTML table:\n\n"
            f"{original_schema}\n\n"
            "The user has provided the following feedback:\n\n"
            f"\"{feedback}\"\n\n"
            "Please refine and improve the schema based on the feedback. "
            "Make sure to maintain the same JSON structure and format. "
            "Ensure the output is valid and can be parsed as JSON. "
            "Return ONLY the updated schema JSON without any explanations or additional text."
        )
        
        # Initialize the OpenAI client
        llm_client = OpenAIClient()
        model = config.get("llm.schema_refinement_model", "gpt-3.5-turbo-16k")
        temperature = config.get("llm.temperature", 0)
        max_tokens = config.get("schema_refinement.max_tokens", 2000)
        
        # Call the LLM
        response = llm_client.generate(
            prompt=refined_prompt,
            model=model,
            system_message="You are a data schema refinement assistant. Your task is to update data schemas based on user feedback. Output only valid JSON without markdown code blocks (```). Return only the JSON object with no additional text.",
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Extract the refined schema
        return response["content"].strip()
    
    # Process with the new refiner
    feedback_dict = {"user_feedback": feedback}
    result = refiner.refine_schema(schema_obj, feedback_dict)
    
    # Return the string version of the schema
    if "error" in result:
        return original_schema
    else:
        return result["raw_output"]
