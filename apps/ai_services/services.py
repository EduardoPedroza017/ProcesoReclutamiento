"""
Servicios de IA - Integración con Claude API (Anthropic)
"""
import time
import json
from typing import Dict, List, Any, Optional
from django.conf import settings
from anthropic import Anthropic, APIError
import PyPDF2
import docx
import io


class ClaudeService:
    """
    Servicio para interactuar con Claude API
    """
    
    def __init__(self):
        # Verificar que tengamos la API key
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key or api_key == '':
            raise ValueError("ANTHROPIC_API_KEY no está configurada en settings")
        
        # Inicializar sin parámetros problemáticos
        import os
        os.environ['ANTHROPIC_API_KEY'] = api_key
        
        # Crear cliente básico sin opciones extra
        from anthropic import Anthropic
        self.client = Anthropic()
        
        self.model = "claude-sonnet-4-5-20250929"
        self.max_tokens = 4096
    
    def _make_api_call(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        Realiza una llamada a la API de Claude
        
        Returns:
            Dict con: response, tokens_input, tokens_output, execution_time, success, error
        """
        start_time = time.time()
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages,
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.client.messages.create(**kwargs)
            
            execution_time = time.time() - start_time
            
            return {
                "response": response.content[0].text,
                "tokens_input": response.usage.input_tokens,
                "tokens_output": response.usage.output_tokens,
                "execution_time": execution_time,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            # Log más detallado del error
            print(f"❌ Error en llamada a Claude API: {error_msg}")
            
            return {
                "response": "",
                "tokens_input": 0,
                "tokens_output": 0,
                "execution_time": execution_time,
                "success": False,
                "error": error_msg
            }


class CVAnalyzerService(ClaudeService):
    """
    Servicio para analizar CVs usando Claude
    """
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extrae texto de un PDF"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            raise Exception(f"Error extrayendo texto del PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extrae texto de un DOCX"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extrayendo texto del DOCX: {str(e)}")
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extrae texto de un archivo (PDF o DOCX)"""
        if file_path.lower().endswith('.pdf'):
            return self.extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            return self.extract_text_from_docx(file_path)
        else:
            raise Exception("Formato de archivo no soportado. Use PDF o DOCX")
    
    def analyze_cv(self, cv_text: str) -> Dict[str, Any]:
        """
        Analiza un CV y extrae información estructurada
        
        Args:
            cv_text: Texto del CV
            
        Returns:
            Dict con el análisis completo
        """
        
        system_prompt = """Eres un experto reclutador y analista de CVs. Tu tarea es analizar CVs y extraer información estructurada de forma precisa y profesional."""
        
        prompt = f"""Analiza el siguiente CV y proporciona un análisis completo en formato JSON con la siguiente estructura:

{{
  "datos_personales": {{
    "nombre_completo": "string",
    "email": "string",
    "telefono": "string",
    "ciudad": "string",
    "estado": "string"
  }},
  "educacion": [
    {{
      "nivel": "string",
      "institucion": "string",
      "carrera": "string",
      "anio_graduacion": "string"
    }}
  ],
  "experiencia_laboral": [
    {{
      "empresa": "string",
      "puesto": "string",
      "periodo": "string",
      "descripcion": "string",
      "logros": ["string"]
    }}
  ],
  "habilidades_tecnicas": ["string"],
  "habilidades_blandas": ["string"],
  "idiomas": [
    {{
      "idioma": "string",
      "nivel": "string"
    }}
  ],
  "certificaciones": ["string"],
  "años_experiencia_total": number,
  "resumen_profesional": "string",
  "fortalezas": ["string"],
  "areas_de_mejora": ["string"],
  "posiciones_recomendadas": ["string"]
}}

CV:
{cv_text}

IMPORTANTE: Responde ÚNICAMENTE con el JSON válido, sin texto adicional antes o después."""

        result = self._make_api_call(prompt, system_prompt)
        
        if result["success"]:
            try:
                # Limpiar la respuesta de markdown antes de parsear JSON
                response_text = result["response"].strip()
                
                # Remover bloques de código markdown si existen
                if response_text.startswith("```json"):
                    response_text = response_text[7:]  # Quitar ```json
                elif response_text.startswith("```"):
                    response_text = response_text[3:]  # Quitar ```
                
                if response_text.endswith("```"):
                    response_text = response_text[:-3]  # Quitar ``` del final
                
                response_text = response_text.strip()
                
                # Parsear JSON limpio
                parsed_data = json.loads(response_text)
                
                return {
                    "parsed_data": parsed_data,
                    "summary": parsed_data.get("resumen_profesional", ""),
                    "strengths": parsed_data.get("fortalezas", []),
                    "weaknesses": parsed_data.get("areas_de_mejora", []),
                    "recommended_positions": parsed_data.get("posiciones_recomendadas", []),
                    "tokens_input": result["tokens_input"],
                    "tokens_output": result["tokens_output"],
                    "execution_time": result["execution_time"],
                    "success": True,
                    "error": None
                }
            except json.JSONDecodeError as e:
                return {
                    "parsed_data": {},
                    "summary": result["response"],
                    "strengths": [],
                    "weaknesses": [],
                    "recommended_positions": [],
                    "tokens_input": result["tokens_input"],
                    "tokens_output": result["tokens_output"],
                    "execution_time": result["execution_time"],
                    "success": False,
                    "error": f"Error parseando JSON: {str(e)}"
                }
        else:
            return {
                "parsed_data": {},
                "summary": "",
                "strengths": [],
                "weaknesses": [],
                "recommended_positions": [],
                "tokens_input": 0,
                "tokens_output": 0,
                "execution_time": result["execution_time"],
                "success": False,
                "error": result["error"]
            }


class MatchingService(ClaudeService):
    """
    Servicio para realizar matching entre candidatos y perfiles
    """
    
    def calculate_matching(
        self,
        candidate_data: Dict[str, Any],
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calcula el matching entre un candidato y un perfil
        
        Args:
            candidate_data: Datos del candidato
            profile_data: Datos del perfil
            
        Returns:
            Dict con el análisis de matching
        """
        
        system_prompt = """Eres un experto en reclutamiento y análisis de compatibilidad entre candidatos y posiciones laborales. Tu tarea es evaluar objetivamente qué tan bien encaja un candidato con un perfil de puesto."""
        
        prompt = f"""Analiza el siguiente candidato y perfil de puesto, y proporciona un análisis de compatibilidad en formato JSON:

CANDIDATO:
{json.dumps(candidate_data, indent=2, ensure_ascii=False)}

PERFIL DE PUESTO:
{json.dumps(profile_data, indent=2, ensure_ascii=False)}

Proporciona tu análisis en el siguiente formato JSON:

{{
  "puntuacion_general": number (0-100),
  "puntuaciones_especificas": {{
    "habilidades_tecnicas": number (0-100),
    "habilidades_blandas": number (0-100),
    "experiencia": number (0-100),
    "educacion": number (0-100),
    "ubicacion": number (0-100),
    "salario": number (0-100)
  }},
  "analisis": "string (análisis detallado de la compatibilidad)",
  "fortalezas_del_match": ["string"],
  "gaps_o_brechas": ["string"],
  "recomendaciones": "string",
  "fit_cultural_estimado": number (0-100),
  "decision_recomendada": "string (Altamente recomendado / Recomendado / Considerar / No recomendado)"
}}

IMPORTANTE: Responde ÚNICAMENTE con el JSON válido, sin texto adicional."""

        result = self._make_api_call(prompt, system_prompt)
        
        if result["success"]:
            try:
                # Limpiar la respuesta de markdown antes de parsear JSON
                response_text = result["response"].strip()
                
                # Remover bloques de código markdown si existen
                if response_text.startswith("```json"):
                    response_text = response_text[7:]  # Quitar ```json
                elif response_text.startswith("```"):
                    response_text = response_text[3:]  # Quitar ```
                
                if response_text.endswith("```"):
                    response_text = response_text[:-3]  # Quitar ``` del final
                
                response_text = response_text.strip()
                
                # Parsear JSON limpio
                matching_data = json.loads(response_text)
                        
                return {
                    "overall_score": matching_data.get("puntuacion_general", 0),
                    "technical_skills_score": matching_data.get("puntuaciones_especificas", {}).get("habilidades_tecnicas", 0),
                    "soft_skills_score": matching_data.get("puntuaciones_especificas", {}).get("habilidades_blandas", 0),
                    "experience_score": matching_data.get("puntuaciones_especificas", {}).get("experiencia", 0),
                    "education_score": matching_data.get("puntuaciones_especificas", {}).get("educacion", 0),
                    "location_score": matching_data.get("puntuaciones_especificas", {}).get("ubicacion", 0),
                    "salary_score": matching_data.get("puntuaciones_especificas", {}).get("salario", 0),
                    "matching_analysis": matching_data.get("analisis", ""),
                    "strengths": matching_data.get("fortalezas_del_match", []),
                    "gaps": matching_data.get("gaps_o_brechas", []),
                    "recommendations": matching_data.get("recomendaciones", ""),
                    "tokens_input": result["tokens_input"],
                    "tokens_output": result["tokens_output"],
                    "execution_time": result["execution_time"],
                    "success": True,
                    "error": None
                }
            except json.JSONDecodeError as e:
                return {
                    "overall_score": 0,
                    "technical_skills_score": 0,
                    "soft_skills_score": 0,
                    "experience_score": 0,
                    "education_score": 0,
                    "location_score": 0,
                    "salary_score": 0,
                    "matching_analysis": result["response"],
                    "strengths": [],
                    "gaps": [],
                    "recommendations": "",
                    "tokens_input": result["tokens_input"],
                    "tokens_output": result["tokens_output"],
                    "execution_time": result["execution_time"],
                    "success": False,
                    "error": f"Error parseando JSON: {str(e)}"
                }
        else:
            return {
                "overall_score": 0,
                "technical_skills_score": 0,
                "soft_skills_score": 0,
                "experience_score": 0,
                "education_score": 0,
                "location_score": 0,
                "salary_score": 0,
                "matching_analysis": "",
                "strengths": [],
                "gaps": [],
                "recommendations": "",
                "tokens_input": 0,
                "tokens_output": 0,
                "execution_time": result["execution_time"],
                "success": False,
                "error": result["error"]
            }


class ProfileGenerationService(ClaudeService):
    """
    Servicio para generar perfiles de reclutamiento desde transcripciones
    """
    
    def generate_profile_from_transcription(
        self,
        transcription: str,
        client_name: str = "",
        additional_notes: str = ""
    ) -> Dict[str, Any]:
        """
        Genera un perfil de reclutamiento desde una transcripción
        
        Args:
            transcription: Transcripción de la reunión
            client_name: Nombre del cliente (opcional)
            additional_notes: Notas adicionales (opcional)
            
        Returns:
            Dict con los datos del perfil generado
        """
        
        system_prompt = """Eres un experto consultor de reclutamiento. Tu tarea es analizar transcripciones de reuniones con clientes y generar perfiles de reclutamiento profesionales y detallados."""
        
        prompt = f"""Analiza la siguiente transcripción de una reunión de reclutamiento y genera un perfil completo de posición en formato JSON:

CLIENTE: {client_name if client_name else "No especificado"}

TRANSCRIPCIÓN:
{transcription}

{f"NOTAS ADICIONALES:\n{additional_notes}\n" if additional_notes else ""}

Genera el perfil en el siguiente formato JSON:

{{
  "titulo_posicion": "string",
  "descripcion_posicion": "string (detallada)",
  "departamento": "string",
  "ubicacion": {{
    "ciudad": "string",
    "estado": "string",
    "es_remoto": boolean,
    "es_hibrido": boolean
  }},
  "salario": {{
    "minimo": number,
    "maximo": number,
    "moneda": "MXN",
    "periodo": "mensual o anual"
  }},
  "requisitos": {{
    "nivel_educacion": "string",
    "años_experiencia": number,
    "edad_minima": number (opcional),
    "edad_maxima": number (opcional)
  }},
  "habilidades_tecnicas": ["string"],
  "habilidades_blandas": ["string"],
  "idiomas": [
    {{
      "idioma": "string",
      "nivel": "string"
    }}
  ],
  "beneficios": "string",
  "requisitos_adicionales": "string",
  "numero_posiciones": number,
  "prioridad": "low, medium, high, urgent",
  "tipo_servicio": "normal o specialized",
  "fecha_deseada_inicio": "YYYY-MM-DD (opcional)",
  "deadline": "YYYY-MM-DD (opcional)"
}}

IMPORTANTE: Responde ÚNICAMENTE con el JSON válido, sin texto adicional."""

        result = self._make_api_call(prompt, system_prompt)
        
        if result["success"]:
            try:
                profile_data = json.loads(result["response"])
                
                return {
                    "profile_data": profile_data,
                    "tokens_input": result["tokens_input"],
                    "tokens_output": result["tokens_output"],
                    "execution_time": result["execution_time"],
                    "success": True,
                    "error": None
                }
            except json.JSONDecodeError as e:
                return {
                    "profile_data": {},
                    "tokens_input": result["tokens_input"],
                    "tokens_output": result["tokens_output"],
                    "execution_time": result["execution_time"],
                    "success": False,
                    "error": f"Error parseando JSON: {str(e)}\n\nRespuesta: {result['response']}"
                }
        else:
            return {
                "profile_data": {},
                "tokens_input": 0,
                "tokens_output": 0,
                "execution_time": result["execution_time"],
                "success": False,
                "error": result["error"]
            }


class SummarizationService(ClaudeService):
    """
    Servicio para generar resúmenes y reportes
    """
    
    def summarize_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un resumen ejecutivo de un candidato
        
        Args:
            candidate_data: Datos completos del candidato
            
        Returns:
            Dict con el resumen
        """
        
        system_prompt = """Eres un experto reclutador. Tu tarea es crear resúmenes ejecutivos concisos y profesionales de candidatos."""
        
        prompt = f"""Genera un resumen ejecutivo profesional del siguiente candidato en 2-3 párrafos:

CANDIDATO:
{json.dumps(candidate_data, indent=2, ensure_ascii=False)}

El resumen debe:
1. Destacar lo más relevante de su experiencia
2. Mencionar sus habilidades clave
3. Indicar su propuesta de valor única
4. Ser conciso pero informativo (150-200 palabras)

Proporciona SOLO el resumen, sin encabezados ni formato adicional."""

        result = self._make_api_call(prompt, system_prompt)
        
        return {
            "summary": result["response"] if result["success"] else "",
            "tokens_input": result["tokens_input"],
            "tokens_output": result["tokens_output"],
            "execution_time": result["execution_time"],
            "success": result["success"],
            "error": result["error"]
        }
    
    def generate_candidate_report(
        self,
        candidates_data: List[Dict[str, Any]],
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Genera un reporte comparativo de múltiples candidatos
        
        Args:
            candidates_data: Lista de datos de candidatos
            profile_data: Datos del perfil
            
        Returns:
            Dict con el reporte
        """
        
        system_prompt = """Eres un consultor senior de reclutamiento. Tu tarea es crear reportes ejecutivos comparativos de candidatos para una posición."""
        
        prompt = f"""Genera un reporte ejecutivo comparativo de los siguientes candidatos para la posición especificada:

POSICIÓN:
{json.dumps(profile_data, indent=2, ensure_ascii=False)}

CANDIDATOS:
{json.dumps(candidates_data, indent=2, ensure_ascii=False)}

El reporte debe incluir:
1. Resumen de la posición
2. Análisis comparativo de los candidatos
3. Top 3 candidatos recomendados con justificación
4. Recomendaciones finales

Usa un formato profesional y estructurado."""

        result = self._make_api_call(prompt, system_prompt)
        
        return {
            "report": result["response"] if result["success"] else "",
            "tokens_input": result["tokens_input"],
            "tokens_output": result["tokens_output"],
            "execution_time": result["execution_time"],
            "success": result["success"],
            "error": result["error"]
        }