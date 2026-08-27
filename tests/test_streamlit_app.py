import unittest

from streamlit.testing.v1 import AppTest


class StreamlitAppSmokeTest(unittest.TestCase):
    def test_all_public_modules_render_without_exceptions(self):
        app = AppTest.from_file("../streamlit_app.py", default_timeout=20).run()
        self.assertFalse(app.exception)
        for page in [
            "Customer growth",
            "Market demand",
            "Cuisine opportunity",
            "Decision Lab",
            "Data reliability",
        ]:
            app.radio[0].set_value(page).run()
            self.assertFalse(app.exception, f"{page} raised a Streamlit exception")


if __name__ == "__main__":
    unittest.main()
