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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])