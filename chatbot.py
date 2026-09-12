class Chatbot:

    def __init__(self):
        self.name = "Power System Assistant"

    def reply(self, message, system_data=None):
        message = message.lower().strip()

        if not message:
            return "Please enter a question."

        if "hello" in message or "hi" in message:
            return (
                "Hello! I am your Power System Assistant. "
                "You can ask me about transmission lines, "
                "ABCD parameters, ACSR conductors, voltage regulation, "
                "losses, efficiency, and your calculated results."
            )

        if "abcd" in message:
            return (
                "The ABCD parameters A, B, C and D are used to represent "
                "the electrical behavior of a transmission line. They "
                "relate sending-end voltage and current to receiving-end "
                "voltage and current."
            )

        if "acsr" in message:
            return (
                "ACSR stands for Aluminium Conductor Steel Reinforced. "
                "It is commonly used for overhead transmission lines "
                "because it provides good conductivity and mechanical strength."
            )

        if "voltage regulation" in message:
            if system_data and system_data.get("regulation") != "—":
                regulation = system_data["regulation"]

                return (
                    f"The current voltage regulation is {regulation}%. "
                    "Voltage regulation indicates the change in receiving-end "
                    "voltage between no-load and loaded conditions."
                )

            return (
                "Voltage regulation indicates the change in receiving-end "
                "voltage between no-load and loaded conditions."
            )

        if "loss" in message:
            if system_data and system_data.get("losses") != "—":
                return (
                    f"The current calculated line loss is "
                    f"{system_data['losses']} kW."
                )

            return "Calculate the system first so I can tell you the line losses."

        if "efficiency" in message:
            if system_data and system_data.get("efficiency") != "—":
                return (
                    f"The current transmission efficiency is "
                    f"{system_data['efficiency']}%."
                )

            return "Calculate the system first so I can report the efficiency."

        if "receiving voltage" in message or "receiving end voltage" in message:
            if system_data and system_data.get("vr") != "—":
                return (
                    f"The calculated receiving-end voltage is "
                    f"{system_data['vr']} kV."
                )

            return "Calculate the system first to obtain the receiving-end voltage."

        if "model" in message:
            if system_data and system_data.get("model") != "—":
                return (
                    f"The selected transmission-line model is "
                    f"{system_data['model']}."
                )

            return "Calculate the system first so I can identify the selected model."

        return (
            "I don't have an answer for that yet. "
            "Try asking about ABCD parameters, ACSR, voltage regulation, "
            "receiving voltage, line losses, efficiency, or the selected model."
        )