from dotenv import load_dotenv
import os
from openai import OpenAI
import random

load_dotenv()
# fresh start logu
with open("game_log.txt", "w", encoding="utf-8") as f:
    f.write("=== AI MAFIA GAME LOG ===\n")
client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

# Logovaci funkce - nahrazuje "print()" protoze v txt souboru je to prehlednejsi
def log(text):
    print(text)
    with open("game_log.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")

# jednotliví hráči - jejich role + vnitřní charakteristika
players = {
    "Hanzo": {"role": "killer", "personality": "calm, manipulative"},
    "Baltazar": {"role": "civilian", "personality": "distrustful"},
    "Thomas": {"role": "civilian", "personality": "smart"},
    "Jessica": {"role": "civilian", "personality": "quiet"},
}

alive = list(players.keys())

def ask_ai(name, situation):
    role = players[name]["role"]
    personality = players[name]["personality"]
    alive_players = ", ".join(alive)

    prompt = f"""
        You are NOT an AI assistant. You are a PLAYER in a Mafia social deduction game.
        your name is: {name}
        your role is: {role}
        you have this personality: {personality}

        The rules you must follow are:
        - Don't admit your true role.
        - Answer maximally with 3 sentences.
        - Speak naturally.

        Alive players: {alive_players}

        Situation: {situation}
    """

    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content.strip()

# den - verejna debata
log("\nDAY - DISCUSSION")

statements = {}

for name in alive:
    reply = ask_ai(name, "It is morning. Who do you suspect and why?")
    statements[name] = reply 
    log(f"{name}: {reply}\n")

# hlasovani
log("\nVOTING")
votes = {}

for name in alive:
    others = [p for p in alive if p != name]
    reply = ask_ai(name, f"This is what other players have said:\n{statements}\n\nWho do you want to eliminate? Answer with only a name.")
    vote = reply.split()[0]
    if vote in others:
        votes[vote] = votes.get(vote, 0) + 1
    
    log(f"{name} votes for: {vote}\n")

lynched = max(votes, key=votes.get)
log(f"\n{lynched} was voted out.")
log(f"His/Her role was: {players[lynched]['role']}")