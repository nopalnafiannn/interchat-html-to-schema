# html_schema_converter/agents/schema_refiner.py
from html_schema_converter.llm.openai_client import OpenAIClient
from html_schema_converter.config import config
from html_schema_converter.utils.metrics import track_metrics

def refine_schema(original_schema: str, feedback: str) -> str:
    """
    Refine the generated schema by combining the original schema with human feedback.
    Sends a refined prompt to the LLM and returns the updated schema.
    
    Args:
        original_schema: The original schema as a string (JSON or YAML)
        feedback: User feedback text
        
    Returns:
        Refined schema as a string in the same format as the input
    """
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
        system_message="You are a data schema refinement assistant. Your task is to update data schemas based on user feedback.",
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    # Extract the refined schema
    refined_schema = response["content"].strip()
    
    return refined_schema
