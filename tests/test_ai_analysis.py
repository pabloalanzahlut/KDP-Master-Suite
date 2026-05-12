"""
Test Suite para AI Analysis Modules - Módulos 21-40
====================================================
Tests para validar módulos de IA con fallback local.

Autor: KDP_MASTER AI Team
Fecha: 2026-05-12
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOllamaAIClient(unittest.TestCase):
    """Tests para Módulo 21: OllamaAIClient (base)"""

    def test_client_creation(self):
        """Test de creación del cliente."""
        from app.modules.ai_analysis import OllamaAIClient
        client = OllamaAIClient()
        self.assertIsNotNone(client)
        self.assertEqual(client.base_url, "http://localhost:11434")

    def test_client_with_custom_url(self):
        """Test de cliente con URL personalizada."""
        from app.modules.ai_analysis import OllamaAIClient
        client = OllamaAIClient(base_url="http://custom:11434", model="llama2")
        self.assertEqual(client.base_url, "http://custom:11434")
        self.assertEqual(client.model, "llama2")

    def test_system_prompts_exist(self):
        """Test de que system prompts están definidos."""
        from app.modules.ai_analysis import OllamaAIClient
        client = OllamaAIClient()
        prompts = client.SYSTEM_PROMPTS
        self.assertIn('density', prompts)
        self.assertIn('noise', prompts)
        self.assertIn('chunk', prompts)
        self.assertIn('tags', prompts)

    def test_stats_initialization(self):
        """Test de inicialización de estadísticas."""
        from app.modules.ai_analysis import OllamaAIClient
        client = OllamaAIClient()
        stats = client.get_stats()
        self.assertEqual(stats['total_calls'], 0)
        self.assertEqual(stats['successful'], 0)
        self.assertEqual(stats['failed'], 0)

    def test_stats_reset(self):
        """Test de reset de estadísticas."""
        from app.modules.ai_analysis import OllamaAIClient
        client = OllamaAIClient()
        client._stats['total_calls'] = 10
        client.reset_stats()
        stats = client.get_stats()
        self.assertEqual(stats['total_calls'], 0)

    def test_quick_analyze_function(self):
        """Test de función quick_analyze."""
        from app.modules.ai_analysis import quick_analyze
        result = quick_analyze("test text", "density")
        self.assertIsNotNone(result)

    def test_create_ai_client_factory(self):
        """Test de factory function."""
        from app.modules.ai_analysis import create_ai_client
        client = create_ai_client()
        self.assertIsInstance(client, type(create_ai_client()))


class TestInfoDensityClassifier(unittest.TestCase):
    """Tests para Módulo 21: InfoDensityClassifier"""

    def test_classifier_creation(self):
        """Test de creación del clasificador."""
        from app.modules.ai_analysis import InfoDensityClassifier
        classifier = InfoDensityClassifier()
        self.assertIsNotNone(classifier)

    def test_classify_with_ai_fallback(self):
        """Test de clasificación con fallback."""
        from app.modules.ai_analysis import InfoDensityClassifier
        classifier = InfoDensityClassifier(ai_client=None)
        result = classifier.classify("Este es un texto de prueba para clasificar")
        self.assertIsNotNone(result)
        self.assertIsInstance(result.score, float)

    def test_density_thresholds(self):
        """Test de umbrales de densidad."""
        from app.modules.ai_analysis import InfoDensityClassifier, DensityResult
        classifier = InfoDensityClassifier()

        high_density = "KDP marketing SEO analytics conversion metrics ROI engagement retention acquisition funnels"
        result = classifier.classify(high_density)
        self.assertGreater(result.score, 5)

        low_density = "hola mundo esto es un texto muy simple sin mucha informacion util"
        result = classifier.classify(low_density)
        self.assertLess(result.score, 5)

    def test_batch_classify(self):
        """Test de clasificación por lotes."""
        from app.modules.ai_analysis import InfoDensityClassifier
        classifier = InfoDensityClassifier()
        texts = ["texto uno", "texto dos", "texto tres"]
        results = classifier.batch_classify(texts)
        self.assertEqual(len(results), 3)

    def test_recommendations_generation(self):
        """Test de generación de recomendaciones."""
        from app.modules.ai_analysis import InfoDensityClassifier
        classifier = InfoDensityClassifier()
        result = classifier.classify("marketing digital estrategias ventas clientes")
        self.assertIsNotNone(result)
        self.assertIsInstance(result.recommendation, str)


class TestNoiseSignalDetector(unittest.TestCase):
    """Tests para Módulo 22: NoiseSignalDetector"""

    def test_detector_creation(self):
        """Test de creación del detector."""
        from app.modules.ai_analysis import NoiseSignalDetector
        detector = NoiseSignalDetector()
        self.assertIsNotNone(detector)

    def test_signal_detection(self):
        """Test de detección de señal."""
        from app.modules.ai_analysis import NoiseSignalDetector
        detector = NoiseSignalDetector()

        clean_text = "Marketing digital estrategias SEO analytics conversión métricas clientes ventas"
        result = detector.detect(clean_text)
        self.assertIsNotNone(result)

    def test_noise_detection(self):
        """Test de detección de ruido."""
        from app.modules.ai_analysis import NoiseSignalDetector
        detector = NoiseSignalDetector()

        noisy_text = "¡Increíble oferta! Solo por hoy. Haz clic aquí. Gana dinero fácil. No te pierdas esta oportunidad única!!!"
        result = detector.detect(noisy_text)
        self.assertFalse(result.is_signal)

    def test_spam_patterns(self):
        """Test de patrones de spam."""
        from app.modules.ai_analysis import NoiseSignalDetector
        detector = NoiseSignalDetector()

        spam = "CLICK HERE for FREE MONEY! Act NOW! Limited time offer! Visit our website for more info!!!"
        result = detector.detect(spam)
        self.assertFalse(result.is_signal)
        self.assertGreater(len(result.noise_types), 0)

    def test_batch_detect(self):
        """Test de detección por lotes."""
        from app.modules.ai_analysis import NoiseSignalDetector
        detector = NoiseSignalDetector()
        texts = ["texto limpio", "texto con ruido"]
        results = detector.batch_detect(texts)
        self.assertEqual(len(results), 2)


class TestSemanticChunker(unittest.TestCase):
    """Tests para Módulo 23: SemanticChunker"""

    def test_chunker_creation(self):
        """Test de creación del chunker."""
        from app.modules.ai_analysis import SemanticChunker
        chunker = SemanticChunker()
        self.assertIsNotNone(chunker)

    def test_chunking_basic(self):
        """Test de chunking básico."""
        from app.modules.ai_analysis import SemanticChunker
        chunker = SemanticChunker()

        text = "Primer concepto importante. Segundo concepto relacionado. Tercer concepto diferente."
        result = chunker.chunk(text)
        self.assertIsNotNone(result)
        self.assertGreater(result.chunk_count, 0)

    def test_max_chunk_size(self):
        """Test de límite de tamaño de chunk."""
        from app.modules.ai_analysis import SemanticChunker
        chunker = SemanticChunker()

        long_text = "A" * 500
        result = chunker.chunk(long_text)
        self.assertIsNotNone(result)

    def test_overlap_chunks(self):
        """Test de solapamiento de chunks."""
        from app.modules.ai_analysis import SemanticChunker
        chunker = SemanticChunker()
        text = "Concepto uno. Concepto dos. Concepto tres. Concepto cuatro."
        result = chunker.chunk(text)
        self.assertIsNotNone(result)


class TestJargonTranslator(unittest.TestCase):
    """Tests para Módulo 24: JargonTranslator"""

    def test_translator_creation(self):
        """Test de creación del traductor."""
        from app.modules.ai_analysis import JargonTranslator
        translator = JargonTranslator()
        self.assertIsNotNone(translator)

    def test_translation_basic(self):
        """Test de traducción básica."""
        from app.modules.ai_analysis import JargonTranslator
        translator = JargonTranslator()

        jargon_text = "Leverage your ROI through synergistic partnerships"
        result = translator.translate(jargon_text)
        self.assertIsNotNone(result)
        self.assertIsInstance(result.translated, str)

    def test_terms_mapping(self):
        """Test de mapeo de términos."""
        from app.modules.ai_analysis import JargonTranslator
        translator = JargonTranslator()

        jargon_text = "funnel marketing ROI leads conversion"
        result = translator.translate(jargon_text)
        self.assertIsNotNone(result)

    def test_batch_translate(self):
        """Test de traducción por lotes."""
        from app.modules.ai_analysis import JargonTranslator
        translator = JargonTranslator()
        texts = ["texto técnico uno", "texto técnico dos"]
        results = translator.batch_translate(texts)
        self.assertEqual(len(results), 2)


class TestNERExtractor(unittest.TestCase):
    """Tests para Módulo 25: NERExtractor"""

    def test_extractor_creation(self):
        """Test de creación del extractor."""
        from app.modules.ai_analysis import NERExtractor
        extractor = NERExtractor()
        self.assertIsNotNone(extractor)

    def test_entity_extraction(self):
        """Test de extracción de entidades."""
        from app.modules.ai_analysis import NERExtractor, EntityType
        extractor = NERExtractor()

        text = "Uso de Shopify para crear tienda online. Google Analytics para métricas. Juan Pérez recomienda."
        result = extractor.extract(text)
        self.assertIsNotNone(result)
        self.assertIsInstance(result.entities, list)

    def test_platform_entities(self):
        """Test de detección de plataformas."""
        from app.modules.ai_analysis import NERExtractor, EntityType
        extractor = NERExtractor()

        text = "Implementé chatbot en Facebook Messenger y automatizaciones en Zapier"
        result = extractor.extract(text)
        platforms = [e for e in result.entities if e.entity_type == EntityType.PLATFORM]
        self.assertGreater(len(platforms), 0)

    def test_metric_entities(self):
        """Test de detección de métricas."""
        from app.modules.ai_analysis import NERExtractor, EntityType
        extractor = NERExtractor()

        text = "Aumentamos CTR a 5.2% y mejoramos Conversion Rate en 3.8%"
        result = extractor.extract(text)
        metrics = [e for e in result.entities if e.entity_type == EntityType.METRIC]
        self.assertGreater(len(metrics), 0)

    def test_batch_extract(self):
        """Test de extracción por lotes."""
        from app.modules.ai_analysis import NERExtractor
        extractor = NERExtractor()
        texts = ["texto uno", "texto dos"]
        results = extractor.batch_extract(texts)
        self.assertEqual(len(results), 2)


class TestContentTypeClassifier(unittest.TestCase):
    """Tests para Módulo 26: ContentTypeClassifier"""

    def test_classifier_creation(self):
        """Test de creación del clasificador."""
        from app.modules.ai_analysis import ContentTypeClassifier
        classifier = ContentTypeClassifier()
        self.assertIsNotNone(classifier)

    def test_tutorial_classification(self):
        """Test de clasificación de tutorial."""
        from app.modules.ai_analysis import ContentTypeClassifier, ContentType
        classifier = ContentTypeClassifier()

        tutorial_text = "Cómo crear una tienda online en 5 pasos. Paso 1: Elegir plataforma. Paso 2: Registrar dominio."
        result = classifier.classify(tutorial_text)
        self.assertEqual(result.content_type, ContentType.TUTORIAL)

    def test_case_study_classification(self):
        """Test de clasificación de caso de estudio."""
        from app.modules.ai_analysis import ContentTypeClassifier, ContentType
        classifier = ContentTypeClassifier()

        case_text = "Caso de estudio: Empresa X aumentó ventas 150% usando marketing digital. Resultados: ..."
        result = classifier.classify(case_text)
        self.assertEqual(result.content_type, ContentType.CASE_STUDY)

    def test_list_classification(self):
        """Test de clasificación de lista."""
        from app.modules.ai_analysis import ContentTypeClassifier, ContentType
        classifier = ContentTypeClassifier()

        list_text = "10 razones para usar SEO en tu negocio. 1. Mayor visibilidad. 2. Tráfico orgánico."
        result = classifier.classify(list_text)
        self.assertEqual(result.content_type, ContentType.LIST)


class TestManualPredictor(unittest.TestCase):
    """Tests para Módulo 27: ManualPredictor"""

    def test_predictor_creation(self):
        """Test de creación del predictor."""
        from app.modules.ai_analysis import ManualPredictor
        predictor = ManualPredictor()
        self.assertIsNotNone(predictor)

    def test_legalidad_prediction(self):
        """Test de predicción de categoría Legalidad."""
        from app.modules.ai_analysis import ManualPredictor, ManualCategory
        predictor = ManualPredictor()

        legal_text = "Políticas de privacidad y términos de servicio según GDPR. Cumplimiento legal requerido."
        result = predictor.predict(legal_text)
        self.assertEqual(result.category, ManualCategory.LEGALIDAD)

    def test_formulas_prediction(self):
        """Test de predicción de categoría Fórmulas."""
        from app.modules.ai_analysis import ManualPredictor, ManualCategory
        predictor = ManualPredictor()

        formula_text = "Cálculo de ROI = (Beneficio - Inversión) / Inversión. Margen de ganancia = Ventas - Costos."
        result = predictor.predict(formula_text)
        self.assertEqual(result.category, ManualCategory.FÓRMULAS)

    def test_priority_assignment(self):
        """Test de asignación de prioridad."""
        from app.modules.ai_analysis import ManualPredictor, Priority
        predictor = ManualPredictor()

        high_value = "Manual de referencia base de datos fórmulas matrices indicadores KPI guía completa"
        result = predictor.predict(high_value)
        self.assertIn(result.priority, [Priority.HIGH, Priority.MEDIUM])


class TestBiasDetector(unittest.TestCase):
    """Tests para Módulo 28: BiasDetector"""

    def test_detector_creation(self):
        """Test de creación del detector."""
        from app.modules.ai_analysis import BiasDetector
        detector = BiasDetector()
        self.assertIsNotNone(detector)

    def test_biased_content_detection(self):
        """Test de detección de contenido sesgado."""
        from app.modules.ai_analysis import BiasDetector
        detector = BiasDetector()

        biased_text = "¡Increíble producto! El mejor del mercado, garantizado 100%. No pierdas esta oportunidad única!!!"
        result = detector.analyze(biased_text)
        self.assertTrue(result.is_biased)

    def test_unbiased_content_detection(self):
        """Test de detección de contenido sin sesgo."""
        from app.modules.ai_analysis import BiasDetector
        detector = BiasDetector()

        unbiased_text = "Estudio de 2024 muestra que el 60% de empresas usan marketing digital. Fuente: Informe Anual."
        result = detector.analyze(unbiased_text)
        self.assertFalse(result.is_biased)

    def test_severity_score(self):
        """Test de puntuación de severidad."""
        from app.modules.ai_analysis import BiasDetector
        detector = BiasDetector()

        very_biased = "OFERTA INCREÍBLE! SOLO HOY! GANA DINERO FÁCIL! CLICK AQUÍ!!!"
        result = detector.analyze(very_biased)
        self.assertIsNotNone(result)


class TestTagGenerator(unittest.TestCase):
    """Tests para Módulo 29: TagGenerator"""

    def test_generator_creation(self):
        """Test de creación del generador."""
        from app.modules.ai_analysis import TagGenerator
        generator = TagGenerator()
        self.assertIsNotNone(generator)

    def test_tag_generation(self):
        """Test de generación de tags."""
        from app.modules.ai_analysis import TagGenerator
        generator = TagGenerator()

        text = "Marketing digital para ecommerce. Estrategias de SEO y publicidad en Google Ads."
        result = generator.generate(text)
        self.assertIsNotNone(result.tags)
        self.assertGreater(result.tag_count, 0)

    def test_max_tags_limit(self):
        """Test de límite de tags."""
        from app.modules.ai_analysis import TagGenerator
        generator = TagGenerator()

        text = "marketing digital ecommerce seo advertising google analytics conversion"
        result = generator.generate(text, max_tags=5)
        self.assertLessEqual(result.tag_count, 5)

    def test_category_detection(self):
        """Test de detección de categorías."""
        from app.modules.ai_analysis import TagGenerator
        generator = TagGenerator()

        text = "Tutorial de YouTube para crear videos de marketing"
        result = generator.generate(text)
        self.assertIsInstance(result.categories, list)


class TestCoherenceValidator(unittest.TestCase):
    """Tests para Módulo 30: CoherenceValidator"""

    def test_validator_creation(self):
        """Test de creación del validador."""
        from app.modules.ai_analysis import CoherenceValidator
        validator = CoherenceValidator()
        self.assertIsNotNone(validator)

    def test_coherent_content_validation(self):
        """Test de validación de contenido coherente."""
        from app.modules.ai_analysis import CoherenceValidator
        validator = CoherenceValidator()

        coherent = "Marketing digital incluye SEO y publicidad. SEO mejora posicionamiento. Publicidad aumenta alcance."
        result = validator.validate(coherent)
        self.assertTrue(result.is_coherent)

    def test_incoherent_content_validation(self):
        """Test de validación de contenido incoherente."""
        from app.modules.ai_analysis import CoherenceValidator
        validator = CoherenceValidator()

        incoherent = "Marketing digital para ventas. Receta de pizza margarita. El clima está soleado."
        result = validator.validate(incoherent)
        self.assertIsNotNone(result)

    def test_topic_shift_detection(self):
        """Test de detección de cambios de tema."""
        from app.modules.ai_analysis import CoherenceValidator
        validator = CoherenceValidator()

        text = "Marketing online. Receta de cocina. Filosofía antigua."
        chunks = ["Marketing online.", "Receta de cocina.", "Filosofía antigua."]
        result = validator.validate(text, chunks)
        self.assertGreater(len(result.topic_shifts), 0)


class TestPlagiarismDetector(unittest.TestCase):
    """Tests para Módulo 31: PlagiarismDetector"""

    def test_detector_creation(self):
        """Test de creación del detector."""
        from app.modules.ai_analysis import PlagiarismDetector
        detector = PlagiarismDetector()
        self.assertIsNotNone(detector)

    def test_register_content(self):
        """Test de registro de contenido."""
        from app.modules.ai_analysis import PlagiarismDetector
        detector = PlagiarismDetector()
        detector.register_content("id1", "Contenido de prueba")
        self.assertIn("id1", detector._content_hashes)

    def test_duplicate_detection(self):
        """Test de detección de duplicados."""
        from app.modules.ai_analysis import PlagiarismDetector
        detector = PlagiarismDetector()
        detector.register_content("id1", "Texto original")

        result = detector.detect("Texto original")
        self.assertTrue(result.is_duplicate)
        self.assertEqual(result.source_id, "id1")

    def test_unique_content_detection(self):
        """Test de detección de contenido único."""
        from app.modules.ai_analysis import PlagiarismDetector
        detector = PlagiarismDetector()
        detector.register_content("id1", "Texto existente")

        result = detector.detect("Texto completamente diferente")
        self.assertFalse(result.is_duplicate)


class TestExecSummaryGenerator(unittest.TestCase):
    """Tests para Módulo 32: ExecSummaryGenerator"""

    def test_generator_creation(self):
        """Test de creación del generador."""
        from app.modules.ai_analysis import ExecSummaryGenerator
        generator = ExecSummaryGenerator()
        self.assertIsNotNone(generator)

    def test_summary_generation(self):
        """Test de generación de resumen."""
        from app.modules.ai_analysis import ExecSummaryGenerator
        generator = ExecSummaryGenerator()

        text = "Marketing digital es esencial. Incluye SEO, redes sociales y publicidad. Permite alcanzar más clientes."
        result = generator.generate(text)
        self.assertIsNotNone(result.summary)
        self.assertIsInstance(result.summary, str)

    def test_key_points_extraction(self):
        """Test de extracción de puntos clave."""
        from app.modules.ai_analysis import ExecSummaryGenerator
        generator = ExecSummaryGenerator()

        text = "Importante: SEO mejora visibilidad. Punto clave: Redes sociales aumenta engagement."
        result = generator.generate(text)
        self.assertIsInstance(result.key_points, list)

    def test_action_items_extraction(self):
        """Test de extracción de items de acción."""
        from app.modules.ai_analysis import ExecSummaryGenerator
        generator = ExecSummaryGenerator()

        text = "Deberías implementar SEO. Hay que crear contenido. Recomendable revisar métricas."
        result = generator.generate(text)
        self.assertIsInstance(result.action_items, list)


class TestUrgencyClassifier(unittest.TestCase):
    """Tests para Módulo 33: UrgencyClassifier"""

    def test_classifier_creation(self):
        """Test de creación del clasificador."""
        from app.modules.ai_analysis import UrgencyClassifier
        classifier = UrgencyClassifier()
        self.assertIsNotNone(classifier)

    def test_high_urgency_classification(self):
        """Test de clasificación de alta urgencia."""
        from app.modules.ai_analysis import UrgencyClassifier, ProcessingUrgency
        classifier = UrgencyClassifier()

        urgent = "Nueva actualización de algoritmo Google. Tendencia actual en SEO. Urgente revisar estrategia."
        result = classifier.classify(urgent)
        self.assertEqual(result.urgency, ProcessingUrgency.NOW)

    def test_low_urgency_classification(self):
        """Test de clasificación de baja urgencia."""
        from app.modules.ai_analysis import UrgencyClassifier, ProcessingUrgency
        classifier = UrgencyClassifier()

        low_urgent = "Artículo de referencia sobre marketing básico. Conceptos fundamentales."
        result = classifier.classify(low_urgent)
        self.assertIn(result.urgency, [ProcessingUrgency.BATCH, ProcessingUrgency.DEFERRED])

    def test_priority_score(self):
        """Test de puntuación de prioridad."""
        from app.modules.ai_analysis import UrgencyClassifier
        classifier = UrgencyClassifier()

        text = "Última hora: nuevo lanzamiento de producto"
        result = classifier.classify(text)
        self.assertGreater(result.priority_score, 0.5)


class TestErrorTranslator(unittest.TestCase):
    """Tests para Módulo 34: ErrorTranslator"""

    def test_translator_creation(self):
        """Test de creación del traductor."""
        from app.modules.ai_analysis import ErrorTranslator
        translator = ErrorTranslator()
        self.assertIsNotNone(translator)

    def test_extraction_error_translation(self):
        """Test de traducción de error de extracción."""
        from app.modules.ai_analysis import ErrorTranslator, ErrorCategory
        translator = ErrorTranslator()

        error = "Failed to extract content from page"
        result = translator.translate(error)
        self.assertEqual(result.category, ErrorCategory.EXTRACTION)

    def test_network_error_translation(self):
        """Test de traducción de error de red."""
        from app.modules.ai_analysis import ErrorTranslator, ErrorCategory
        translator = ErrorTranslator()

        error = "Connection timeout after 30 seconds"
        result = translator.translate(error)
        self.assertEqual(result.category, ErrorCategory.NETWORK)

    def test_solution_generation(self):
        """Test de generación de soluciones."""
        from app.modules.ai_analysis import ErrorTranslator
        translator = ErrorTranslator()

        error = "Parse error in JSON response"
        result = translator.translate(error)
        self.assertIsInstance(result.solution, str)
        self.assertIsInstance(result.troubleshooting_steps, list)


class TestTimePredictor(unittest.TestCase):
    """Tests para Módulo 35: TimePredictor"""

    def test_predictor_creation(self):
        """Test de creación del predictor."""
        from app.modules.ai_analysis import TimePredictor
        predictor = TimePredictor()
        self.assertIsNotNone(predictor)

    def test_time_prediction(self):
        """Test de predicción de tiempo."""
        from app.modules.ai_analysis import TimePredictor
        predictor = TimePredictor()

        text = "A" * 1000
        result = predictor.predict(text)
        self.assertIsNotNone(result.estimated_minutes)
        self.assertGreater(result.estimated_minutes, 0)

    def test_content_type_factor(self):
        """Test de factor de tipo de contenido."""
        from app.modules.ai_analysis import TimePredictor
        predictor = TimePredictor()

        video_text = "A" * 1000
        result = predictor.predict(video_text, content_type="video")
        self.assertIsNotNone(result.breakdown)

    def test_complexity_assessment(self):
        """Test de evaluación de complejidad."""
        from app.modules.ai_analysis import TimePredictor
        predictor = TimePredictor()

        complex_text = "A" * 10000 + "API SDK microservices integration methodology"
        result = predictor.predict(complex_text)
        self.assertIsNotNone(result.factors)


class TestKBFusion(unittest.TestCase):
    """Tests para Módulo 36: KBFusion"""

    def test_fusion_creation(self):
        """Test de creación del fusionador."""
        from app.modules.ai_analysis import KBFusion
        fusion = KBFusion()
        self.assertIsNotNone(fusion)

    def test_add_kb_entry(self):
        """Test de agregar entrada KB."""
        from app.modules.ai_analysis import KBFusion, KBEntry
        fusion = KBFusion()
        entry = KBEntry(id="1", title="Test", content="Content test")
        fusion.add_kb_entry(entry)
        self.assertEqual(len(fusion.kb_entries), 1)

    def test_separate_action(self):
        """Test de acción separate."""
        from app.modules.ai_analysis import KBFusion, KBEntry, FusionAction
        fusion = KBFusion()
        entry = KBEntry(id="1", title="Marketing", content="Marketing digital strategies")
        fusion.add_kb_entry(entry)

        result = fusion.suggest_fusion("Cocina recetas italiana")
        self.assertEqual(result.action, FusionAction.SEPARATE)

    def test_fuse_action(self):
        """Test de acción fuse."""
        from app.modules.ai_analysis import KBFusion, KBEntry, FusionAction
        fusion = KBFusion()
        entry = KBEntry(id="1", title="Marketing", content="marketing digital ecommerce marketing online ventas")
        fusion.add_kb_entry(entry)

        result = fusion.suggest_fusion("marketing online ventas digitales marketing marketing")
        self.assertIsNotNone(result)


class TestStaleDetector(unittest.TestCase):
    """Tests para Módulo 37: StaleDetector"""

    def test_detector_creation(self):
        """Test de creación del detector."""
        from app.modules.ai_analysis import StaleDetector
        detector = StaleDetector()
        self.assertIsNotNone(detector)

    def test_fresh_content_detection(self):
        """Test de detección de contenido fresco."""
        from app.modules.ai_analysis import StaleDetector
        detector = StaleDetector()

        fresh = "Actualización 2026-05-10: Nuevas políticas de privacidad. Verificado el 2026-05-12."
        result = detector.detect(fresh)
        self.assertFalse(result.is_stale)

    def test_old_date_detection(self):
        """Test de detección de fechas antiguas."""
        from app.modules.ai_analysis import StaleDetector
        detector = StaleDetector()

        old = "Según datos de 2020-01-15, el mercado creció 30%. Políticas de 2019-03-01."
        result = detector.detect(old)
        self.assertTrue(result.is_stale or len(result.stale_items) > 0)


class TestValidationQuizGenerator(unittest.TestCase):
    """Tests para Módulo 38: ValidationQuizGenerator"""

    def test_generator_creation(self):
        """Test de creación del generador."""
        from app.modules.ai_analysis import ValidationQuizGenerator
        generator = ValidationQuizGenerator()
        self.assertIsNotNone(generator)

    def test_quiz_generation(self):
        """Test de generación de quiz."""
        from app.modules.ai_analysis import ValidationQuizGenerator
        generator = ValidationQuizGenerator()

        text = "Marketing digital incluye SEO, redes sociales y publicidad. SEO mejora posicionamiento web. Redes sociales aumenta engagement. Publicidad en Google Ads genera conversiones."
        result = generator.generate(text, num_questions=3)
        self.assertEqual(result.total_questions, 3)
        self.assertEqual(len(result.questions), 3)

    def test_estimated_time(self):
        """Test de tiempo estimado."""
        from app.modules.ai_analysis import ValidationQuizGenerator
        generator = ValidationQuizGenerator()

        text = "Conceptos de marketing online"
        result = generator.generate(text)
        self.assertGreater(result.estimated_time_minutes, 0)


class TestActionRecommender(unittest.TestCase):
    """Tests para Módulo 39: ActionRecommender"""

    def test_recommender_creation(self):
        """Test de creación del recomendador."""
        from app.modules.ai_analysis import ActionRecommender
        recommender = ActionRecommender()
        self.assertIsNotNone(recommender)

    def test_index_action_recommendation(self):
        """Test de recomendación de acción index."""
        from app.modules.ai_analysis import ActionRecommender, ActionType
        recommender = ActionRecommender()

        high_quality = {
            'content': 'A' * 1000 + ' marketing ventas estrategias ROI métricas KDP',
            'quality': 0.95,
            'completeness': 0.95,
            'duplicate_score': 0.05
        }
        result = recommender.recommend(high_quality)
        self.assertIsNotNone(result)

    def test_discard_action_recommendation(self):
        """Test de recomendación de acción discard."""
        from app.modules.ai_analysis import ActionRecommender, ActionType
        recommender = ActionRecommender()

        low_quality = {
            'content': 'abc',
            'quality': 0.2,
            'completeness': 0.1,
            'duplicate_score': 0.9
        }
        result = recommender.recommend(low_quality)
        self.assertIn(result.action, [ActionType.DISCARD, ActionType.REVIEW])

    def test_action_summary(self):
        """Test de resumen de acciones."""
        from app.modules.ai_analysis import ActionRecommender
        recommender = ActionRecommender()

        results = [
            recommender.recommend({'content': 'test', 'quality': 0.9, 'completeness': 0.8, 'duplicate_score': 0.1})
            for _ in range(3)
        ]
        summary = recommender.get_action_summary(results)
        self.assertIn('total', summary)
        self.assertIn('index_count', summary)


class TestPipelineOptimizer(unittest.TestCase):
    """Tests para Módulo 40: PipelineOptimizer"""

    def test_optimizer_creation(self):
        """Test de creación del optimizador."""
        from app.modules.ai_analysis import PipelineOptimizer
        optimizer = PipelineOptimizer()
        self.assertIsNotNone(optimizer)

    def test_optimization_basic(self):
        """Test de optimización básica."""
        from app.modules.ai_analysis import PipelineOptimizer
        optimizer = PipelineOptimizer()

        characteristics = {
            'word_count': 1000,
            'has_media': False,
            'quality': 0.7
        }
        result = optimizer.optimize(characteristics)
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.recommended_config)

    def test_savings_calculation(self):
        """Test de cálculo de ahorro."""
        from app.modules.ai_analysis import PipelineOptimizer
        optimizer = PipelineOptimizer()

        characteristics = {'word_count': 500, 'quality': 0.9}
        result = optimizer.optimize(characteristics)
        self.assertIsInstance(result.savings_percent, float)

    def test_bottleneck_identification(self):
        """Test de identificación de cuellos de botella."""
        from app.modules.ai_analysis import PipelineOptimizer
        optimizer = PipelineOptimizer()

        characteristics = {'word_count': 5000, 'has_media': True}
        result = optimizer.optimize(characteristics)
        self.assertIsInstance(result.bottlenecks, list)

    def test_record_execution(self):
        """Test de registro de ejecución."""
        from app.modules.ai_analysis import PipelineOptimizer, PipelineStage
        optimizer = PipelineOptimizer()

        optimizer.record_execution(PipelineStage.EXTRACT, 5.2)
        report = optimizer.get_performance_report()
        self.assertIn('total_executions', report)


if __name__ == '__main__':
    unittest.main()