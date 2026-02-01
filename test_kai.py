"""Quick test of Kai."""
from kai.main import Kai

kai = Kai()

# Test chat
r1 = kai.chat("Hi!")
print("User: Hi!")
print("Kai:", r1)

r2 = kai.chat("How are you?")
print("\nUser: How are you?")
print("Kai:", r2)

# Test status
s = kai.get_status()
print("\n--- Status ---")
print("Mode:", s["kai"]["mode"])
print("Emotions:", s["kai"]["emotion_vector"])

print("\nOK - Kai is working!")
