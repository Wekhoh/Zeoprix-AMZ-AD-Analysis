"""Tests for KPI calculator pure functions"""

from backend.services.kpi_calculator import (
    calc_acos,
    calc_cpc,
    calc_ctr,
    calc_cvr,
    calc_roas,
)


class TestCalcCtr:
    def test_normal_case(self):
        result = calc_ctr(clicks=50, impressions=1000)
        assert result == round(50 / 1000, 6)

    def test_zero_impressions(self):
        result = calc_ctr(clicks=10, impressions=0)
        assert result is None


class TestCalcCpc:
    def test_normal_case(self):
        result = calc_cpc(spend=25.0, clicks=50)
        assert result == 0.50

    def test_zero_clicks(self):
        result = calc_cpc(spend=25.0, clicks=0)
        assert result is None


class TestCalcRoas:
    def test_normal_case(self):
        result = calc_roas(sales=150.0, spend=25.0)
        assert result == 6.0

    def test_zero_spend(self):
        result = calc_roas(sales=150.0, spend=0.0)
        assert result is None


class TestCalcAcos:
    def test_normal_case(self):
        result = calc_acos(spend=25.0, sales=150.0)
        assert result == round(25.0 / 150.0, 4)

    def test_zero_sales(self):
        result = calc_acos(spend=25.0, sales=0.0)
        assert result is None


class TestCalcCvr:
    def test_normal_case(self):
        result = calc_cvr(orders=5, clicks=50)
        assert result == 0.1

    def test_zero_clicks(self):
        result = calc_cvr(orders=5, clicks=0)
        assert result is None
