from __future__ import annotations

from pathlib import Path
import sys
import unittest


APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from app_core.data import (  # noqa: E402
    BUFFER_ORDER,
    PORTFOLIO_PATH,
    REGION_DIR,
    TEAM_IMAGES_DIR,
    TEAM_PATH,
    group_portfolio,
    load_portfolio,
    load_region_data,
    load_team,
    resolve_region_path,
)
from app_core.ui import format_decimal, format_integer, format_soles  # noqa: E402
from app_core.visuals import (  # noqa: E402
    build_buffer_chart,
    build_influence_map,
    build_timeline_chart,
)


class PortfolioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.portfolio = load_portfolio()
        cls.grouped = group_portfolio(cls.portfolio)

    def test_expected_portfolio_structure(self) -> None:
        self.assertEqual(len(self.portfolio), 6)
        self.assertEqual(set(self.grouped), {1, 2, 3})
        self.assertEqual([len(self.grouped[key]) for key in (1, 2, 3)], [3, 1, 2])

    def test_every_database_relation_exists(self) -> None:
        for project in self.portfolio:
            path = resolve_region_path(project.database_name)
            self.assertTrue(path.is_file(), project.database_name)
            self.assertTrue(path.resolve().is_relative_to(APP_DIR.resolve()))

    def test_application_is_self_contained(self) -> None:
        for path in (PORTFOLIO_PATH, TEAM_PATH, REGION_DIR, TEAM_IMAGES_DIR):
            self.assertTrue(path.resolve().is_relative_to(APP_DIR.resolve()))
            self.assertTrue(path.exists(), path)

        outside_path = APP_DIR.parent / "outside.xlsx"
        with self.assertRaises(ValueError):
            load_portfolio(outside_path)
        with self.assertRaises(ValueError):
            load_team(outside_path)

    def test_team_catalog_and_images(self) -> None:
        members = load_team()
        self.assertEqual(len(members), 3)
        self.assertEqual(len({member.image_path for member in members}), 3)
        for member in members:
            self.assertTrue(member.full_name)
            self.assertTrue(member.linkedin_url.startswith("https://www.linkedin.com/"))
            self.assertIsNotNone(member.image_path)
            self.assertTrue(member.image_path.is_file())
            self.assertTrue(member.image_path.resolve().is_relative_to(APP_DIR.resolve()))

    def test_region_data_are_clean_and_complete(self) -> None:
        for project in self.portfolio:
            region, diagnostics = load_region_data(
                project.database_name, project.latitude, project.longitude
            )
            self.assertFalse(region.empty)
            self.assertTrue(region["LATITUD"].between(-20, 0.5).all())
            self.assertTrue(region["LONGITUD"].between(-82.5, -67).all())
            self.assertTrue(region["DIST_KM"].between(0, 350).all())
            self.assertEqual(int(region["CODIGO_UNICO"].duplicated().sum()), 0)
            self.assertEqual((int(region["ANO"].min()), int(region["ANO"].max())), (2017, 2026))
            self.assertGreater(diagnostics.output_rows, 0)

    def test_map_has_timeline_and_no_star_marker(self) -> None:
        project = self.grouped[1][0]
        region, _ = load_region_data(
            project.database_name, project.latitude, project.longitude
        )
        figure = build_influence_map(region, project, within_50_km=True)
        self.assertEqual([frame.name for frame in figure.frames], [str(year) for year in range(2017, 2027)])
        symbols = [getattr(trace.marker, "symbol", None) for trace in figure.data if hasattr(trace, "marker")]
        self.assertNotIn("star", symbols)
        self.assertIn("circle", symbols)
        self.assertTrue(any(trace.name == f"Logo {project.app_name}" for trace in figure.data))
        self.assertTrue(figure.layout.sliders)
        self.assertTrue(figure.layout.updatemenus)
        function_trace = next(
            trace
            for trace in figure.data
            if trace.legendgroup == "functions"
            and trace.customdata is not None
            and len(trace.customdata)
        )
        self.assertEqual(len(function_trace.customdata[0]), 7)
        self.assertIn("S/ %{customdata[4]:,.2f} MM", function_trace.hovertemplate)

    def test_numeric_formats_use_commas_points_and_mm(self) -> None:
        self.assertEqual(format_integer(1_234_567), "1,234,567")
        self.assertEqual(format_decimal(1_234_567.891, 2), "1,234,567.89")
        self.assertEqual(format_soles(1_234_567_890), "S/ 1,234.57 MM")

    def test_complementary_charts_keep_full_axis_labels(self) -> None:
        project = self.grouped[1][0]
        region, _ = load_region_data(
            project.database_name, project.latitude, project.longitude
        )
        view = region.loc[region["DIST_KM"].le(50)]
        timeline = build_timeline_chart(view, project.color)
        expected_years = tuple(str(year) for year in range(2017, 2027))
        self.assertEqual(tuple(timeline.layout.xaxis.ticktext), expected_years)
        self.assertTrue(timeline.layout.xaxis.automargin)
        self.assertGreaterEqual(timeline.layout.margin.b, 40)

        buffers = build_buffer_chart(view)
        self.assertEqual(tuple(buffers.layout.yaxis.ticktext), BUFFER_ORDER)
        self.assertTrue(buffers.layout.yaxis.automargin)
        self.assertGreaterEqual(buffers.layout.margin.l, 80)


if __name__ == "__main__":
    unittest.main()
