"""
Tests for Scheduler Extensions - Days of Week and Templates
=============================================================
Tests for the new allowed_days field and task templates.
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path


class TestScheduleTaskDaysOfWeek:
    """Tests for ScheduleTask allowed_days field"""

    def test_default_allowed_days(self):
        """Test that default allowed_days is all days"""
        from app.core.scheduler import ScheduleTask, DAYS_OF_WEEK
        task = ScheduleTask(name="Test Task")
        assert task.allowed_days == DAYS_OF_WEEK

    def test_custom_allowed_days(self):
        """Test setting custom allowed_days"""
        from app.core.scheduler import ScheduleTask
        task = ScheduleTask(
            name="Weekday Task",
            allowed_days=['mon', 'tue', 'wed', 'thu', 'fri']
        )
        assert task.allowed_days == ['mon', 'tue', 'wed', 'thu', 'fri']

    def test_empty_allowed_days_defaults_to_all(self):
        """Test that empty allowed_days defaults to all days"""
        from app.core.scheduler import ScheduleTask, DAYS_OF_WEEK
        task = ScheduleTask(name="Test Task", allowed_days=[])
        assert task.allowed_days == DAYS_OF_WEEK

    def test_to_dict_includes_allowed_days(self):
        """Test that to_dict includes allowed_days"""
        from app.core.scheduler import ScheduleTask
        task = ScheduleTask(
            name="Test Task",
            allowed_days=['mon', 'tue']
        )
        task_dict = task.to_dict()
        assert 'allowed_days' in task_dict
        assert task_dict['allowed_days'] == ['mon', 'tue']

    def test_from_dict_restores_allowed_days(self):
        """Test that from_dict restores allowed_days"""
        from app.core.scheduler import ScheduleTask
        data = {
            'task_id': 'test-123',
            'name': 'Test Task',
            'task_type': 'download',
            'schedule_type': 'interval',
            'interval_minutes': 60,
            'daily_time': '03:00',
            'multiple_times': [],
            'allowed_days': ['sat', 'sun'],
            'enabled': True,
            'last_run': None,
            'next_run': None,
            'event_trigger': None,
            'max_retries': 3,
            'retry_count': 0,
            'auto_integrate_kb': True,
            'max_active_tasks': 10
        }
        task = ScheduleTask.from_dict(data)
        assert task.allowed_days == ['sat', 'sun']


class TestDayValidation:
    """Tests for day of week validation"""

    def test_is_day_allowed_all_days(self):
        """Test allowed check with all days"""
        from app.core.scheduler import ScheduleManager, ScheduleTask
        manager = ScheduleManager()
        task = ScheduleTask(name="Test")
        now = datetime.now()
        assert manager._is_day_allowed(task, now) is True

    def test_is_day_allowed_specific_days(self):
        """Test allowed check with specific days"""
        from app.core.scheduler import ScheduleManager, ScheduleTask
        manager = ScheduleManager()
        task = ScheduleTask(
            name="Weekday Task",
            allowed_days=['mon', 'tue', 'wed', 'thu', 'fri']
        )
        now = datetime.now()
        day_of_week = now.weekday()
        is_allowed = manager._is_day_allowed(task, now)
        if day_of_week < 5:
            assert is_allowed is True
        else:
            assert is_allowed is False


class TestCalculateNextRunWithDays:
    """Tests for _calculate_next_run with allowed_days"""

    def test_next_run_weekday_only_monday(self):
        """Test that next_run skips to Monday when current day not allowed"""
        from app.core.scheduler import ScheduleManager, ScheduleTask
        manager = ScheduleManager()

        now = datetime.now()
        if now.weekday() == 5:
            saturday = now
            task = ScheduleTask(
                name="Weekday Task",
                schedule_type='interval',
                interval_minutes=60,
                allowed_days=['mon', 'tue', 'wed', 'thu', 'fri']
            )
            next_run = manager._calculate_next_run(task)
            next_dt = datetime.fromisoformat(next_run)
            assert next_dt.weekday() in [0, 1, 2, 3, 4]

    def test_next_run_weekend_only(self):
        """Test that next_run only returns weekend days"""
        from app.core.scheduler import ScheduleManager, ScheduleTask
        manager = ScheduleManager()
        task = ScheduleTask(
            name="Weekend Task",
            schedule_type='daily',
            daily_time='08:00',
            allowed_days=['sat', 'sun']
        )
        next_run = manager._calculate_next_run(task)
        next_dt = datetime.fromisoformat(next_run)
        assert next_dt.weekday() in [5, 6]


class TestTaskTemplates:
    """Tests for task templates"""

    def test_task_templates_exist(self):
        """Test that TASK_TEMPLATES dictionary exists"""
        from app.core.scheduler import TASK_TEMPLATES
        assert isinstance(TASK_TEMPLATES, dict)
        assert len(TASK_TEMPLATES) > 0

    def test_template_keys_valid(self):
        """Test that all template keys are valid"""
        from app.core.scheduler import TASK_TEMPLATES
        expected_templates = [
            'daily_download_3am',
            'daily_download_6am',
            'hourly_monitor',
            'half_hourly_monitor',
            'daily_process_2am',
            'weekday_monitor',
            'weekend_download',
            'detect_new_videos'
        ]
        for template_id in expected_templates:
            assert template_id in TASK_TEMPLATES

    def test_template_structure(self):
        """Test template has required fields"""
        from app.core.scheduler import TASK_TEMPLATES
        for template_id, template in TASK_TEMPLATES.items():
            assert 'name' in template
            assert 'task_type' in template
            assert 'schedule_type' in template
            assert 'description' in template

    def test_create_task_from_template(self):
        """Test creating task from template"""
        from app.core.scheduler import create_task_from_template
        task = create_task_from_template('daily_download_3am')
        assert task is not None
        assert task.name == 'Descarga Diaria 3AM'
        assert task.task_type == 'download'
        assert task.schedule_type == 'daily'
        assert task.daily_time == '03:00'

    def test_create_task_from_invalid_template(self):
        """Test that invalid template returns None"""
        from app.core.scheduler import create_task_from_template
        task = create_task_from_template('nonexistent_template')
        assert task is None

    def test_get_available_templates(self):
        """Test get_available_templates returns correct structure"""
        from app.core.scheduler import get_available_templates
        templates = get_available_templates()
        assert isinstance(templates, dict)
        for template_id, info in templates.items():
            assert 'name' in info
            assert 'description' in info
            assert 'task_type' in info
            assert 'schedule_type' in info


class TestScheduleManagerPersistence:
    """Tests for persistence with allowed_days"""

    def test_save_and_load_tasks_with_allowed_days(self):
        """Test saving and loading tasks with allowed_days"""
        from app.core.scheduler import ScheduleManager, ScheduleTask

        manager = ScheduleManager()

        task = ScheduleTask(
            name="Test Task",
            allowed_days=['mon', 'wed', 'fri']
        )
        manager.tasks[task.task_id] = task
        manager._save_tasks()

        manager2 = ScheduleManager()
        loaded_task = manager2.tasks.get(task.task_id)
        assert loaded_task is not None
        assert loaded_task.allowed_days == ['mon', 'wed', 'fri']


class TestDaysOfWeekConstants:
    """Tests for DAYS_OF_WEEK constants"""

    def test_days_of_week_length(self):
        """Test that DAYS_OF_WEEK has 7 days"""
        from app.core.scheduler import DAYS_OF_WEEK
        assert len(DAYS_OF_WEEK) == 7

    def test_days_of_week_values(self):
        """Test correct day values"""
        from app.core.scheduler import DAYS_OF_WEEK
        expected = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        assert DAYS_OF_WEEK == expected

    def test_days_of_week_display_mapping(self):
        """Test DAYS_OF_WEEK_DISPLAY has all days"""
        from app.core.scheduler import DAYS_OF_WEEK_DISPLAY
        assert len(DAYS_OF_WEEK_DISPLAY) == 7
        assert DAYS_OF_WEEK_DISPLAY['mon'] == 'Lunes'
        assert DAYS_OF_WEEK_DISPLAY['sun'] == 'Domingo'


class TestSchedulerMutex:
    """Tests for task mutex/concurrency control"""

    def test_task_locks_initialized(self):
        """Test that task locks are initialized"""
        from app.core.scheduler import ScheduleManager, TaskType
        manager = ScheduleManager()
        assert hasattr(manager, '_task_lock')
        assert hasattr(manager, '_running_tasks')
        assert hasattr(manager, '_task_type_locks')
        assert len(manager._task_type_locks) == 4

    def test_can_execute_task_first_time(self):
        """Test that first task can execute"""
        from app.core.scheduler import ScheduleManager, ScheduleTask
        manager = ScheduleManager()
        task = ScheduleTask(name="Test Task", task_type="download")
        can_execute, reason = manager._can_execute_task(task)
        assert can_execute is True
        assert reason == ""

    def test_can_execute_task_blocks_second(self):
        """Test that second task of same type is blocked"""
        from app.core.scheduler import ScheduleManager, ScheduleTask
        manager = ScheduleManager()

        task1 = ScheduleTask(name="Task 1", task_type="download")
        task2 = ScheduleTask(name="Task 2", task_type="download")

        can1, _ = manager._can_execute_task(task1)
        assert can1 is True

        can2, reason = manager._can_execute_task(task2)
        assert can2 is False
        assert "otra tarea" in reason.lower() or "en ejecución" in reason.lower()

    def test_different_task_types_can_run(self):
        """Test that different task types can run simultaneously"""
        from app.core.scheduler import ScheduleManager, ScheduleTask
        manager = ScheduleManager()

        download_task = ScheduleTask(name="Download", task_type="download")
        monitor_task = ScheduleTask(name="Monitor", task_type="monitor")

        can_download, _ = manager._can_execute_task(download_task)
        can_monitor, _ = manager._can_execute_task(monitor_task)

        assert can_download is True
        assert can_monitor is True

    def test_release_task_lock(self):
        """Test releasing task lock"""
        from app.core.scheduler import ScheduleManager, ScheduleTask
        manager = ScheduleManager()

        task = ScheduleTask(name="Test", task_type="download")
        manager._can_execute_task(task)
        assert task.task_id in manager._running_tasks

        manager._release_task_lock(task)
        assert task.task_id not in manager._running_tasks

    def test_get_running_tasks_info(self):
        """Test get_running_tasks_info method"""
        from app.core.scheduler import ScheduleManager, ScheduleTask
        manager = ScheduleManager()

        task = ScheduleTask(name="Test", task_type="download")
        manager._can_execute_task(task)

        info = manager.get_running_tasks_info()
        assert info['count'] == 1
        assert task.task_id in info['tasks']


class TestSchedulerConfig:
    """Tests for scheduler configuration"""

    def test_scheduler_config_defaults(self):
        """Test SchedulerConfig default values"""
        from app.core.scheduler import SchedulerConfig
        config = SchedulerConfig()
        assert config.default_interval_minutes == 60
        assert config.default_daily_time == "03:00"
        assert config.default_enabled is True
        assert config.notifications_enabled is True
        assert config.auto_start_on_launch is False
        assert config.check_interval_seconds == 60
        assert config.max_concurrent_per_type == 1

    def test_scheduler_config_to_dict(self):
        """Test SchedulerConfig to_dict"""
        from app.core.scheduler import SchedulerConfig
        config = SchedulerConfig(default_interval_minutes=30)
        config_dict = config.to_dict()
        assert config_dict['default_interval_minutes'] == 30

    def test_scheduler_config_from_dict(self):
        """Test SchedulerConfig from_dict"""
        from app.core.scheduler import SchedulerConfig
        data = {'default_interval_minutes': 45, 'notifications_enabled': False}
        config = SchedulerConfig.from_dict(data)
        assert config.default_interval_minutes == 45
        assert config.notifications_enabled is False

    def test_scheduler_config_from_none(self):
        """Test SchedulerConfig from None returns defaults"""
        from app.core.scheduler import SchedulerConfig
        config = SchedulerConfig.from_dict(None)
        assert config.default_interval_minutes == 60

    def test_manager_has_config(self):
        """Test that ScheduleManager has config object"""
        from app.core.scheduler import ScheduleManager
        manager = ScheduleManager()
        assert hasattr(manager, 'config_obj')
        assert isinstance(manager.config_obj, type(manager.get_config()))

    def test_update_config(self):
        """Test updating scheduler config"""
        from app.core.scheduler import ScheduleManager
        manager = ScheduleManager()

        result = manager.update_config(default_interval_minutes=120)
        assert result is True

        config = manager.get_config()
        assert config.default_interval_minutes == 120

    def test_config_persistence(self):
        """Test config is persisted"""
        from app.core.scheduler import ScheduleManager
        manager = ScheduleManager()
        manager.update_config(default_interval_minutes=90)

        manager2 = ScheduleManager()
        config2 = manager2.get_config()
        assert config2.default_interval_minutes == 90

    def test_max_concurrent_updates(self):
        """Test max_concurrent_per_type is updated"""
        from app.core.scheduler import ScheduleManager
        manager = ScheduleManager()
        assert manager.max_concurrent_per_type == 1

        manager.update_config(max_concurrent_per_type=2)
        assert manager.max_concurrent_per_type == 2


class TestConditionTypes:
    """Tests for condition types constants"""

    def test_condition_types_exist(self):
        """Test that CONDITION_TYPES exists"""
        from app.core.scheduler import CONDITION_TYPES
        assert isinstance(CONDITION_TYPES, dict)
        assert 'has_pending_videos' in CONDITION_TYPES
        assert 'disk_space' in CONDITION_TYPES
        assert 'time_window' in CONDITION_TYPES
        assert 'queue_empty' in CONDITION_TYPES

    def test_condition_descriptions_exist(self):
        """Test that CONDITION_DESCRIPTIONS exists"""
        from app.core.scheduler import CONDITION_DESCRIPTIONS
        assert isinstance(CONDITION_DESCRIPTIONS, dict)
        assert len(CONDITION_DESCRIPTIONS) == 4


class TestScheduleTaskCondition:
    """Tests for ScheduleTask condition field"""

    def test_task_condition_default(self):
        """Test that condition defaults to None"""
        from app.core.scheduler import ScheduleTask
        task = ScheduleTask(name="Test")
        assert task.condition is None

    def test_task_condition_custom(self):
        """Test setting custom condition"""
        from app.core.scheduler import ScheduleTask
        task = ScheduleTask(name="Test", condition="has_pending_videos:10")
        assert task.condition == "has_pending_videos:10"

    def test_task_condition_to_dict(self):
        """Test that to_dict includes condition"""
        from app.core.scheduler import ScheduleTask
        task = ScheduleTask(name="Test", condition="disk_space:1000")
        task_dict = task.to_dict()
        assert 'condition' in task_dict
        assert task_dict['condition'] == "disk_space:1000"

    def test_task_condition_from_dict(self):
        """Test that from_dict restores condition"""
        from app.core.scheduler import ScheduleTask, TaskType
        data = {
            'task_id': 'test-123',
            'name': 'Test Task',
            'task_type': TaskType.DOWNLOAD.value,
            'schedule_type': 'interval',
            'interval_minutes': 60,
            'daily_time': '03:00',
            'multiple_times': [],
            'allowed_days': None,
            'condition': 'time_window:09:00-17:00',
            'enabled': True,
            'last_run': None,
            'next_run': None,
            'event_trigger': None,
            'max_retries': 3,
            'retry_count': 0,
            'auto_integrate_kb': True,
            'max_active_tasks': 10
        }
        task = ScheduleTask.from_dict(data)
        assert task.condition == 'time_window:09:00-17:00'


class TestConditionEvaluation:
    """Tests for condition evaluation"""

    def test_evaluate_empty_condition(self):
        """Test that empty condition returns True"""
        from app.core.scheduler import ScheduleManager
        manager = ScheduleManager()
        can_execute, reason = manager._evaluate_condition(None)
        assert can_execute is True

    def test_evaluate_time_window_inside(self):
        """Test time window condition when inside range"""
        from app.core.scheduler import ScheduleManager
        manager = ScheduleManager()
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        time_range = f"{current_time}-{now.replace(hour=(now.hour + 1) % 24).strftime('%H:%M')}"
        can_execute, reason = manager._evaluate_condition(f"time_window:{time_range}")
        assert can_execute is True

    def test_get_available_conditions(self):
        """Test get_available_conditions method"""
        from app.core.scheduler import ScheduleManager
        manager = ScheduleManager()
        conditions = manager.get_available_conditions()
        assert 'types' in conditions
        assert 'descriptions' in conditions
        assert len(conditions['types']) == 4


class TestSchedulerHistoryDB:
    """Tests for scheduler history in database"""

    def test_scheduler_manager_has_db_methods(self):
        """Test that ScheduleManager has DB history methods"""
        from app.core.scheduler import ScheduleManager
        manager = ScheduleManager()
        assert hasattr(manager, 'get_history_from_db')
        assert hasattr(manager, 'get_history_stats_today')
        assert callable(manager.get_history_from_db)
        assert callable(manager.get_history_stats_today)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])