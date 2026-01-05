import json
import os
from pathlib import Path
from typing import Any, cast

import litellm
from dotenv import load_dotenv
from litellm import Choices, ModelResponse
from rich.console import Console

from resume_mate.core.models import MasterProfile

console = Console()


class ResumeAgent:
    def __init__(self, model_name: str = "gpt-5.2", api_key: str | None = None, api_base: str | None = None):
        self.model_name = model_name
        # Prioritize passed key, then LITELLM_API_KEY, then OPENAI_API_KEY
        self.api_key = api_key or os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        # Prioritize passed base, then LITELLM_PROXY_BASE_URL
        self.api_base = api_base or os.getenv("LITELLM_PROXY_BASE_URL")
        
        if not self.api_key:
            console.print("[yellow]Warning: No API key provided or found in environment variables.[/yellow]")

    def _get_completion(self, messages: list[dict[str, str]], json_mode: bool = True) -> Any:
        """Helper to call LiteLLM and parse JSON response."""
        try:
            response = litellm.completion(
                model=self.model_name,
                messages=messages,
                api_key=self.api_key,
                api_base=self.api_base,
                response_format={"type": "json_object"} if json_mode else None,
                stream=False,
            )
            # Cast to ModelResponse to satisfy type checker
            resp = cast(ModelResponse, response)

            if not resp.choices:
                raise ValueError("LLM returned no choices")

            # Cast choice to Choices to avoid StreamingChoices warnings
            choice = cast(Choices, resp.choices[0])
            content = choice.message.content

            if content is None:
                raise ValueError("LLM returned no content")

            if json_mode:
                return json.loads(content)
            return content
        except Exception as e:
            console.print(f"[bold red]Error calling LLM:[/bold red] {e}")
            raise

    def analyze_job_description(self, jd_text: str) -> dict[str, Any]:
        """
        Analyzes the JD to extract keywords, required skills, and key themes.
        """
        prompt = f"""
        You are an expert technical recruiter and resume strategist.
        Analyze the following job description and extract:
        1. Key technical skills required.
        2. Soft skills and cultural fit indicators.
        3. The core mission or primary objective of the role.
        4. Important keywords for ATS optimization.

        Job Description:
        {jd_text}

        Return the result as a valid JSON object with keys: 
        "technical_skills" (list of strings), 
        "soft_skills" (list of strings), 
        "role_mission" (string), 
        "keywords" (list of strings).
        """
        
        return self._get_completion(
            messages=[{"role": "user", "content": prompt}],
            json_mode=True
        )

    def bootstrap_profile(self, raw_text: str, images: list[str] | None = None) -> MasterProfile:
        """
        Extracts candidate information from raw text (e.g., an old resume) 
        and maps it to the MasterProfile schema.
        
        Args:
            raw_text: Text extracted from the file.
            images: Optional list of base64 data URIs (for Vision models).
        """
        schema = MasterProfile.model_json_schema()
        
        prompt_text = f"""
        You are an expert Resume Parser and Career Strategist.
        Your goal is to transform the provided raw resume text (and images if provided) into a structured, high-quality 'Master Profile' JSON object.
        This JSON object is the SINGLE SOURCE OF TRUTH for the candidate's career.

        Raw Resume Text:
        {raw_text}

        MasterProfile JSON Schema:
        {json.dumps(schema, indent=2)}

        CRITICAL INSTRUCTIONS:
        1. **Data Structure**: You MUST output a valid JSON object strictly adhering to the provided schema.
        2. **Dates**: Convert ALL dates to `YYYY-MM` format. If a date is "Present" or "Current", omit the `endDate` (make it null).
        3. **Summary**: If the resume lacks a professional summary, SYNTHESIZE a strong, 3-sentence summary based on the candidate's trajectory and key skills.
        4. **Work Experience**:
           - **Highlights**: Convert paragraph descriptions into crisp, result-oriented bullet points starting with strong action verbs (e.g., "Architected", "Deployed", "Led").
           - **Tech Stack**: For EACH work entry, infer and populate the `techStack` list based on the tools/languages mentioned or implied in the description.
        5. **Projects vs. Work**: Distinguish between professional employment (put in `work`) and side/academic projects (put in `projects`).
        6. **Skills**: Extract ALL technical and soft skills found anywhere in the document.
        7. **Completeness**: Do not truncate information. Capture all relevant details.
        8. **Vision**: If images are provided, use them to understand layout, implied hierarchy, or details missed by text extraction.

        Output ONLY the JSON object.
        """

        if images:
            # Multimodal message construction
            content = [{"type": "text", "text": prompt_text}]
            for img_url in images:
                content.append({"type": "image_url", "image_url": {"url": img_url}})
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that extracts resume data into structured JSON."},
                {"role": "user", "content": content}
            ]
        else:
            # Standard text-only
            messages = [
                {"role": "system", "content": "You are a helpful assistant that extracts resume data into structured JSON."},
                {"role": "user", "content": prompt_text}
            ]

        profile_data = self._get_completion(
            messages=messages,
            json_mode=True
        )

        return MasterProfile(**profile_data)

    def extract_entity(self, text: str, entity_type: str) -> dict[str, Any]:
        """
        Extracts a specific entity (WorkExperience, Project, etc.) from natural language text.
        """
        from resume_mate.core.models import WorkExperience, Project, Education, Skill
        
        type_map = {
            "work": WorkExperience,
            "project": Project,
            "education": Education,
            "skill": Skill
        }
        
        if entity_type not in type_map:
            raise ValueError(f"Unsupported entity type: {entity_type}")
            
        model_class = type_map[entity_type]
        schema = model_class.model_json_schema()
        
        prompt = f"""
        You are an expert resume data extractor. 
        Your task is to parse the following text and convert it into a valid JSON object 
        that conforms to the {entity_type} schema provided below.

        Input Text:
        {text}

        JSON Schema:
        {json.dumps(schema, indent=2)}

        Instructions:
        1. Extract all relevant information and map it to the schema.
        2. Ensure consistent formatting.
        3. Return ONLY the JSON object.
        """
        
        return self._get_completion(
            messages=[{"role": "system", "content": f"You extract {entity_type} data into structured JSON."},
                      {"role": "user", "content": prompt}],
            json_mode=True
        )

    def suggest_improvements(self, profile: MasterProfile) -> dict[str, Any]:
        """
        Analyzes the Master Profile and suggests improvements or identifies gaps.
        """
        profile_dict = profile.model_dump(mode="json")
        
        prompt = f"""
        You are a senior resume consultant. 
        Analyze the following candidate Master Profile and identify:
        1. Gaps in information (e.g., missing tech stacks, brief summaries).
        2. Suggestions for improving bullet points (making them more result-oriented).
        3. Potential skills to add based on the candidate's experience.
        4. Overall professional impression.

        Candidate Master Profile:
        {json.dumps(profile_dict, indent=2)}

        Return the result as a valid JSON object with keys:
        "gaps" (list of strings),
        "suggestions" (list of strings),
        "recommended_skills" (list of strings),
        "overall_critique" (string).
        """
        
        return self._get_completion(
            messages=[{"role": "system", "content": "You are a professional resume critic."},
                      {"role": "user", "content": prompt}],
            json_mode=True
        )

    def tailor_profile(self, profile: MasterProfile, jd_analysis: dict[str, Any], language: str = "English") -> MasterProfile:
        """
        Tailors the Master Profile to fit the analyzed job description.
        Currently focuses on rewriting the summary and filtering/rewriting work experience.
        """
        
        # 1. Tailor the Summary (Basics)
        # 2. Tailor Work Experience (Rewriting highlights)
        
        # For this implementation, we will perform a holistic tailoring of the work experience.
        # We'll ask the LLM to select the most relevant work entries and rewrite their highlights.
        
        # Convert profile to dict for the prompt (excluding some fields to save tokens if needed)
        profile_dict = profile.model_dump(mode="json")
        
        prompt = f"""
        You are a professional resume writer. Your goal is to tailor a candidate's profile to a specific job description.

        Job Analysis:
        {json.dumps(jd_analysis, indent=2)}

        Candidate Master Profile:
        {json.dumps(profile_dict, indent=2)}
        
        Target Language: {language}

        Instructions:
        1. **Summary:** Rewrite the candidate's summary (`basics.summary`) to align with the Role Mission and Keywords. Keep it professional and under 4 lines.
        2. **Work Experience:** 
           - Select the most relevant work experiences.
           - For each selected experience, rewrite the `highlights` to emphasize skills and achievements relevant to the JD.
           - Use the keywords from the analysis.
           - Keep the original `company`, `position`, `startDate`, `endDate`.
           - You may reorder the highlights.
        3. **Skills:** Select and prioritize the `skills` list to match the JD's technical requirements.
        4. **Language:** Ensure the entire resume (summary, bullets, etc.) is written in {language}. If the JD is in a different language, TRANSLATE relevant parts to {language}.

        Return the tailored profile as a JSON object matching the structure of the input Master Profile. 
        ENSURE all fields required by the schema (like 'basics', 'work', 'education', 'skills') are present and correctly formatted.
        """

        tailored_data = self._get_completion(
            messages=[{"role": "user", "content": prompt}],
            json_mode=True
        )
        
        # Validate and return as MasterProfile object
        # We might need to handle potential schema mismatches, but Pydantic is good at that.
        return MasterProfile(**tailored_data)

    def merge_profile(self, current_profile: MasterProfile, new_text: str, images: list[str] | None = None) -> MasterProfile:
        """
        Intelligently merges new resume content into an existing Master Profile.
        
        Args:
            current_profile: The existing MasterProfile object.
            new_text: Text extracted from the new resume file.
            images: Optional list of base64 data URIs (for Vision models).
        """
        schema = MasterProfile.model_json_schema()
        current_data = current_profile.model_dump(mode="json")
        
        prompt_text = f"""
        You are an Expert Data Integrator for resumes.
        Your task is to MERGE new resume data into an existing 'Master Profile' JSON object.

        Current Master Profile:
        {json.dumps(current_data, indent=2)}

        New Resume Input (Text):
        {new_text}

        MasterProfile JSON Schema:
        {json.dumps(schema, indent=2)}

        MERGE RULES:
        1. **MATCH & ENHANCE:** If a Work Experience or Project already exists (fuzzy match on Company/Project Name and Role), UPDATE it with new details (bullets, tech stack) from the new input. Do NOT create duplicates.
        2. **ADD NEW:** If an entry found in the New Resume Input is NOT in the Current Profile, ADD it.
        3. **PRESERVE:** Do NOT remove existing valid details (like old projects, specific bullets) unless the new text explicitly contradicts them or implies they are obsolete. The Master Profile should be a superset of history.
        4. **BASICS UPDATE:** Update contact info, summary, or location if the new input seems more current.
        5. **DATES:** Trust specific dates in the New Input if they are more precise than what is in the Current Profile.
        6. **TECH STACK:** Merge lists of skills/technologies. Avoid duplicates.
        7. **Output Structure:** You MUST output a valid JSON object strictly adhering to the schema.

        Output ONLY the merged JSON object.
        """

        if images:
            # Multimodal message construction
            content = [{"type": "text", "text": prompt_text}]
            for img_url in images:
                content.append({"type": "image_url", "image_url": {"url": img_url}})
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that merges resume data."},
                {"role": "user", "content": content}
            ]
        else:
            # Standard text-only
            messages = [
                {"role": "system", "content": "You are a helpful assistant that merges resume data."},
                {"role": "user", "content": prompt_text}
            ]

        merged_data = self._get_completion(
            messages=messages,
            json_mode=True
        )

        return MasterProfile(**merged_data)


if __name__ == "__main__":
    load_dotenv(".env.local")

    agent = ResumeAgent(
        model_name=os.getenv("LITELLM_MODEL_NAME", "gpt-4o"),
        api_key=os.getenv("LITELLM_API_KEY"),
        api_base=os.getenv("LITELLM_PROXY_BASE_URL"),
    )
    
    jd_text = "We are looking for a Senior Software Engineer with experience in Python, FastAPI, and cloud technologies."
    
    try:
        jd_analysis = agent.analyze_job_description(jd_text)
        console.print(jd_analysis)
    except Exception as e:
        console.print(f"[bold red]Failed to run analysis:[/bold red] {e}")