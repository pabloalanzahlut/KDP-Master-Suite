"""
Módulos IA P6-59: Generación de Plan de Estudio
Crea rutas de aprendizaje estructuradas con videos del canal.
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class StudyPlan:
    """Plan de estudio generado."""
    plan_id: str
    title: str
    description: str
    duration_days: int
    total_videos: int
    total_hours: float
    modules: List[Dict]
    prerequisites: List[str]


@dataclass
class ModulePlan:
    """Módulo individual del plan de estudio."""
    module_id: int
    title: str
    description: str
    videos: List[Dict]
    estimated_hours: float
    difficulty: str


class StudyPlanner:
    """Planificador de rutas de aprendizaje."""

    DIFFICULTY_ORDER = ['beginner', 'intermediate', 'advanced']

    def __init__(self):
        self._plan_count = 0

    def generate_study_plan(
        self,
        videos: List[Dict],
        target_duration_days: int = 30,
        user_level: str = "beginner",
        max_daily_minutes: int = 30
    ) -> StudyPlan:
        """
        P6-59: Genera un plan de estudio estructurado.
        Args:
            videos: Videos disponibles para el plan
            target_duration_days: Días objetivo para completar
            user_level: Nivel actual del usuario
            max_daily_minutes: Minutos diarios disponibles
        Returns:
            StudyPlan con estructura
        """
        self._plan_count += 1

        if not videos:
            return StudyPlan(
                plan_id="empty",
                title="Plan Vacío",
                description="No hay videos disponibles",
                duration_days=0,
                total_videos=0,
                total_hours=0.0,
                modules=[],
                prerequisites=[]
            )

        sorted_videos = self._order_by_learning_path(videos, user_level)

        total_duration = sum(v.get('duration_seconds', 600) for v in sorted_videos)
        total_hours = total_duration / 3600

        daily_videos = (max_daily_minutes / 30) * 2
        total_videos_needed = min(len(sorted_videos), int(target_duration_days * daily_videos))

        selected_videos = sorted_videos[:total_videos_needed]

        modules = self._create_modules(selected_videos, target_duration_days)

        prerequisites = self._extract_prerequisites(selected_videos)

        plan_id = f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return StudyPlan(
            plan_id=plan_id,
            title=f"Plan de Estudio - {target_duration_days} días",
            description=f"Ruta de aprendizaje estructurada para {user_level}s",
            duration_days=target_duration_days,
            total_videos=len(selected_videos),
            total_hours=round(total_hours, 1),
            modules=modules,
            prerequisites=prerequisites
        )

    def _order_by_learning_path(
        self,
        videos: List[Dict],
        user_level: str
    ) -> List[Dict]:
        """Ordena videos por ruta de aprendizaje."""
        level_scores = {
            'beginner': {'beginner': 1, 'intermediate': 2, 'advanced': 3},
            'intermediate': {'beginner': 2, 'intermediate': 1, 'advanced': 2},
            'advanced': {'beginner': 3, 'intermediate': 2, 'advanced': 1}
        }

        scored_videos = []
        for video in videos:
            title = video.get('title', '').lower()
            level = self._detect_level(title)

            score = level_scores.get(user_level, {}).get(level, 2)

            if 'completo' in title or 'full' in title or 'masterclass' in title:
                score -= 0.5

            duration = video.get('duration_seconds', 600)
            if duration < 300:
                score += 0.2

            scored_videos.append((video, score))

        scored_videos.sort(key=lambda x: x[1])
        return [v[0] for v in scored_videos]

    def _detect_level(self, title: str) -> str:
        """Detecta el nivel de un video."""
        if any(kw in title for kw in ['básico', 'beginner', 'intro', 'principiante', 'desde cero']):
            return 'beginner'
        elif any(kw in title for kw in ['avanzado', 'advanced', 'expert', 'profesional']):
            return 'advanced'
        return 'intermediate'

    def _create_modules(
        self,
        videos: List[Dict],
        total_days: int
    ) -> List[Dict]:
        """Crea módulos de estudio."""
        num_modules = min(7, max(3, len(videos) // 5))
        videos_per_module = len(videos) // num_modules

        modules = []
        current_day = 1

        for i in range(num_modules):
            start_idx = i * videos_per_module
            end_idx = start_idx + videos_per_module if i < num_modules - 1 else len(videos)
            module_videos = videos[start_idx:end_idx]

            module_duration = sum(v.get('duration_seconds', 600) for v in module_videos)

            module = {
                'module_id': i + 1,
                'title': f"Módulo {i + 1}: Fundamentos" if i == 0 else f"Módulo {i + 1}: Profundización",
                'description': f" {len(module_videos)} videos - {module_duration / 3600:.1f} horas",
                'videos': [{'title': v.get('title', '')[:40], 'duration': v.get('duration_seconds', 0)} for v in module_videos],
                'estimated_hours': round(module_duration / 3600, 1),
                'difficulty': 'beginner' if i == 0 else 'intermediate' if i < num_modules - 1 else 'advanced'
            }
            modules.append(module)

        return modules

    def _extract_prerequisites(self, videos: List[Dict]) -> List[str]:
        """Extrae prerrequisitos de los videos."""
        prerequisites = set()

        for video in videos[:5]:
            title = video.get('title', '').lower()

            if any(kw in title for kw in ['necesitas', 'required', 'antes', 'before']):
                prerequisites.add('conceptos_básicos')

            if 'python' in title and 'avanzado' in title:
                prerequisites.add('python_básico')

            if 'kdp' in title and 'avanzado' in title:
                prerequisites.add('kdp_básico')

        return list(prerequisites)[:5]

    def export_to_markdown(self, plan: StudyPlan) -> str:
        """Exporta el plan a formato Markdown."""
        md = f"# {plan.title}\n\n"
        md += f"**Descripción:** {plan.description}\n\n"
        md += f"**Duración:** {plan.duration_days} días\n"
        md += f"**Videos Totales:** {plan.total_videos}\n"
        md += f"**Horas Totales:** {plan.total_hours}\n\n"

        md += "## Módulos\n\n"

        for module in plan.modules:
            md += f"### {module['title']}\n"
            md += f"{module['description']}\n"
            md += f"- Dificultad: {module['difficulty']}\n"
            md += f"- Duración: {module['estimated_hours']} horas\n\n"
            md += "Videos:\n"
            for v in module['videos'][:5]:
                md += f"- {v['title']}\n"
            md += "\n"

        if plan.prerequisites:
            md += "## Prerrequisitos\n"
            for prereq in plan.prerequisites:
                md += f"- {prereq}\n"

        return md

    def get_statistics(self) -> Dict:
        """Retorna estadísticas del planificador."""
        return {
            "total_plans": self._plan_count,
            "model": "StudyPlanner v1.0"
        }


def create_study_planner() -> StudyPlanner:
    """Crea una instancia del planificador de estudio."""
    return StudyPlanner()


_global_planner: Optional[StudyPlanner] = None


def get_study_planner() -> StudyPlanner:
    """Obtiene la instancia global del planificador de estudio."""
    global _global_planner
    if _global_planner is None:
        _global_planner = create_study_planner()
    return _global_planner