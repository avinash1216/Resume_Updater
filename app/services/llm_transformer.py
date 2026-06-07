import os
import logging
from typing import Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv

from app.models.schema import Resume

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ResumeLLMTransformer:
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        # If API key is not provided, Client will automatically search for GEMINI_API_KEY in env
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "your_api_key_here":
            logger.warning("No valid GEMINI_API_KEY found. Gemini API calls will fail.")
            
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.model_name = model_name

    def tailor_resume(self, resume_data: Resume, job_description: str) -> Resume:
        """
        Invokes Gemini to rewrite/tailor the experience and project descriptions 
        to match the target job description. Returns a tailored Resume model.
        """
        if not self.client:
            raise RuntimeError("Gemini Client is not initialized. Please configure GEMINI_API_KEY in your .env file.")

        logger.info(f"Requesting Gemini tailoring using model: {self.model_name}...")

        # System instructions to steer the model correctly
        system_instruction = (
            "You are an expert Resume Optimization Engine. Your task is to tailor a candidate's resume "
            "to align with a target Job Description (JD).\n\n"
            "CRITICAL CONSTRAINTS:\n"
            "1. STRICT TRUTH: You must ONLY rewrite the wording of existing work experience bullet points and project descriptions. "
            "You are FORBIDDEN from inventing new jobs, projects, credentials, technologies, or achievements.\n"
            "2. DATA INTEGRITY: Do not modify personal details, company names, job titles, locations, dates, or degrees.\n"
            "3. ALIGNMENT: Focus on highlighting transferrable skills and matching keywords from the JD in the description bullets.\n"
            "4. RESPONSE SCHEMA: You must return the output strictly conforming to the Resume schema."
        )

        prompt = (
            f"Here is the candidate's structured resume:\n"
            f"{resume_data.model_dump_json(indent=2)}\n\n"
            f"Here is the target Job Description (JD):\n"
            f"{job_description}\n\n"
            f"Please optimize the resume bullet points and return the tailored resume."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=Resume,
                    temperature=0.2, # Low temperature for deterministic/grounded output
                ),
            )
            
            # The SDK automatically parses the JSON into the response_schema Pydantic model
            # We can access it directly via response.parsed
            tailored_resume = response.parsed
            if not tailored_resume:
                # Fallback if parsed is not populated for some reason
                import json
                parsed_json = json.loads(response.text)
                tailored_resume = Resume(**parsed_json)
                
            logger.info("Successfully received tailored resume from Gemini!")
            return tailored_resume
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise RuntimeError(f"Gemini API tailoring failed: {str(e)}")
