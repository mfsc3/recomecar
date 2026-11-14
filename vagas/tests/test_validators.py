from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from vagas.validators import validar_cnpj


class CNPJValidatorTests(SimpleTestCase):
    def test_valid_values_are_normalized(self):
        self.assertEqual(validar_cnpj('11222333000181'), '11222333000181')
        self.assertEqual(validar_cnpj('12.345.678/0001-95'), '12345678000195')

    def test_invalid_values_are_rejected(self):
        for value in ('11222333000182', '11111111111111', '123', 'abc', '', '12.345.678/0001-96'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validar_cnpj(value)
