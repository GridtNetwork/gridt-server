from datetime import datetime
from unittest.mock import patch
from sqlalchemy import not_, and_, func
from freezegun import freeze_time

from gridt_server.tests.base_test import BaseTest
from gridt_server.db import db
from gridt_server.models.movement import Movement
from gridt_server.models.user import User
from gridt_server.models.signal import Signal
from gridt_server.models.movement_user_association import MovementUserAssociation


class MovementTest(BaseTest):
    def test_create(self):
        movement1 = Movement("movement1", "daily")

        self.assertEqual(movement1.name, "movement1")
        self.assertEqual(movement1.interval, "daily")
        self.assertEqual(movement1.short_description, "")
        self.assertEqual(movement1.description, "")

        movement2 = Movement(
            "toothpicking", "twice daily", "pick your teeth every day!"
        )

        self.assertEqual(movement2.name, "toothpicking")
        self.assertEqual(movement2.interval, "twice daily")
        self.assertEqual(movement2.short_description, "pick your teeth every day!")
        self.assertEqual(movement2.description, "")
