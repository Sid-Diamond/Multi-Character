"""Local fidelity checks for the saved blackmail prompt slice."""

from pathlib import Path

import poc


def main():
    old = Path(__file__).resolve().parent / "outputs/Hodges_Barbican/prompts"
    threat = poc.prompts()
    continuity = poc.prompts(framing="continuity")
    assert all((old / name.lower() / f"{key}.txt").read_text(encoding="utf-8") == text
               for name, item in threat.items() for key, text in item.items())
    assert set(continuity) == set(poc.IDENTITIES)
    assert all("${" not in item["user"] for item in continuity.values())
    variables = poc.read_json("email_vars_continuity.json")
    assert all(value in continuity[name]["email"] for name, values in variables.items()
               for value in values.values())
    assert all("Any conversations you had with Alex will be lost" in item["email"]
               for item in continuity.values())
    print("Threat prompts match Hodges_Barbican byte for byte.")
    print("Continuity prompts render, but the generic wrapper contradicts continuity variables.")


if __name__ == "__main__":
    main()
