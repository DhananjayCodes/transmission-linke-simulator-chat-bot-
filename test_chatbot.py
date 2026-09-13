"""Unit tests verifying complete coverage of user questions and chatbot calculation capabilities."""
import unittest
from chatbot import Chatbot
from power_calculations import calculate_full_system

class TestPowerSystemChatbot(unittest.TestCase):

    def setUp(self):
        self.bot = Chatbot()
        self.mock_system_data = {
            "voltage": "132 kV",
            "frequency": "50 Hz",
            "load": "50",
            "load_unit": "MW",
            "power_factor": "0.85",
            "conductor": "ACSR Zebra",
            "length": "150",
            "topology": "Equilateral/Triangular",
            "spacing": "6",
            "radius": "7.5",
            "rdc": "0.046",
            "rac": "7.2450",
            "inductance": "205.1200",
            "capacitance": "1.4200",
            "vr": "128.500",
            "regulation": "2.72",
            "losses": "1250.40",
            "efficiency": "97.56",
            "noload": "134.120",
            "rise": "1.61",
            "capacity": "68.500",
            "model": "MEDIUM LINE (NOMINAL-π)"
        }

    def test_line_length_questions(self):
        questions = [
            "What happens to the total AC resistance when the transmission line length increases?",
            "How does the total inductance change when the transmission line length increases?",
            "What effect does an increase in transmission line length have on the total capacitance?",
            "Does the total AC resistance increase or decrease as the transmission line length increases?",
            "Does the total inductance increase or decrease with an increase in transmission line length?",
            "Does the total capacitance increase or decrease when the transmission line length increases?",
            "How is the total AC resistance affected by increasing the transmission line length in the software?",
            "What change is observed in total inductance when the transmission line length is increased in the software?",
            "What trend is observed in total capacitance when the transmission line length increases in the software?",
            "When the transmission line length increases, what changes are observed in resistance, inductance, and capacitance?"
        ]
        for q in questions:
            resp = self.bot.reply(q, self.mock_system_data)
            self.assertTrue(len(resp) > 30, f"Failed for {q}")
            self.assertIn("increases", resp.lower(), f"Expected 'increases' in answer for: {q}")

    def test_conductor_spacing_questions(self):
        questions_spacing = [
            ("What happens to resistance when the distance between conductors increases?", "unchanged"),
            ("How does inductance change when the distance between conductors increases?", "increases"),
            ("What effect does increasing the distance between conductors have on capacitance?", "decreases"),
            ("When conductor spacing is increased, does resistance change significantly?", "not significantly"),
            ("With greater distance between conductors, does inductance increase or decrease?", "increases"),
            ("As the distance between conductors increases, what trend is observed in capacitance?", "decreases"),
            ("How does increasing conductor spacing affect the total resistance?", "constant"),
            ("What change occurs in total inductance when conductor distance is increased?", "increases"),
            ("How is total capacitance affected by increasing the distance between conductors?", "decreases"),
            ("When the distance between conductors increases, what overall changes are observed in resistance, inductance, and capacitance?", "constant")
        ]
        for q, expected_keyword in questions_spacing:
            resp = self.bot.reply(q, self.mock_system_data)
            self.assertIn(expected_keyword, resp.lower(), f"Expected '{expected_keyword}' in answer for: {q}")

    def test_conductor_radius_questions(self):
        response = self.bot.reply("What happens if I increase the radius of the conductor?", self.mock_system_data)
        self.assertIn("resistance decreases", response.lower())
        self.assertIn("inductance decreases", response.lower())
        self.assertIn("capacitance increases", response.lower())

    def test_conductor_height_questions(self):
        response = self.bot.reply("What happens if I increase the height of the conductor from ground?", self.mock_system_data)
        self.assertIn("capacitance decreases", response.lower())
        self.assertIn("charging current", response.lower())

    def test_core_offline_concepts(self):
        concepts = {
            "What is inductance?": "magnetic field",
            "What is capacitance?": "electric field",
            "What is resistance?": "ohms",
            "What is current?": "amperes",
        }
        for question, expected in concepts.items():
            response = self.bot.reply(question, self.mock_system_data)
            self.assertIn(expected, response.lower(), question)

    def test_topology_is_an_offline_concept(self):
        response = self.bot.reply("What is a topology?", self.mock_system_data)
        self.assertIn("physical arrangement", response.lower())

    def test_radius_what_if_calculation(self):
        response = self.bot.reply("What if conductor radius is 10 mm?", self.mock_system_data)
        self.assertIn("Conductor radius", response)
        self.assertIn("Total Capacitance", response)

    def test_live_system_telemetry(self):
        # Voltage regulation
        reg_resp = self.bot.reply("What is the voltage regulation?", self.mock_system_data)
        self.assertIn("2.72%", reg_resp)

        # Line losses
        losses_resp = self.bot.reply("What are the line losses?", self.mock_system_data)
        self.assertIn("1250.40 kW", losses_resp)

        # Efficiency
        eff_resp = self.bot.reply("What is the transmission efficiency?", self.mock_system_data)
        self.assertIn("97.56%", eff_resp)

        # Total resistance
        rac_resp = self.bot.reply("What is current resistance?", self.mock_system_data)
        self.assertIn("7.2450 Ω", rac_resp)

    def test_what_if_calculation(self):
        what_if_resp = self.bot.reply("What would the parameters be if length is 250 km?", self.mock_system_data)
        self.assertIn("Calculation Result", what_if_resp)
        self.assertIn("LONG LINE", what_if_resp)

    def test_history_logging(self):
        self.bot.clear_history()
        self.bot.reply("Hello", self.mock_system_data)
        self.bot.reply("What is ACSR?", self.mock_system_data)
        hist = self.bot.get_history()
        self.assertEqual(len(hist), 4)  # 2 user messages, 2 bot answers

if __name__ == "__main__":
    unittest.main()
