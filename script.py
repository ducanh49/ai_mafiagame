from dotenv import load_dotenv
import os
from openai import OpenAI
import random

load_dotenv()
# fresh start logu + globalni variables
with open("game_log.txt", "w", encoding="utf-8") as f:
    f.write("=== AI MAFIA GAME LOG ===\n")
client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
number_of_days = 1
game_over = False
memory = { "days": [] }


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
    "Clara": {"role": "civilian", "personality": "kind, naive"},
    "Victor" : {"role": "civilian", "personality": "funny, careless"},
    "Elena": { "role": "civilian", "personality": "observant, suspicious" },
    "Marco": { "role": "civilian", "personality": "talkative, impulsive" },
    "Corleone": { "role": "civilian", "personality": "cold, strategic" }
}

def build_memory_summary():
    summary = ""
    for day in memory["days"]:
        summary += f"Day {day['day']}:\n"

        for p, text in day["discussion"].items():
            summary += f"- {p} said: {text}\n"
        if day["votes"]:
            for p, v in day["votes"].items():
                summary += f"- Votes: {p} received {v} vote(s)\n"
        if day["lynched"]:
            summary += f"- {day['lynched']} was lynched\n"
        summary += "\n"
    return summary
    

alive = list(players.keys())
def ask_ai(name, situation):
    role = players[name]["role"]
    personality = players[name]["personality"]
    alive_players = ", ".join(alive)
    memory_summary = build_memory_summary()

    if role == "killer":
        extra = """
                Your goal is survival.
                Avoid leading the discussion too much.
                Occasionally agree with others.
                Make small logical mistakes.
                """
    elif role == "civilian":
        extra = "You may overreact or be uncertain."

    if number_of_days == 1:
        early_game = """
        It is Day 1.
        You have almost no information.
        Your suspicions should be weak, uncertain, or speculative.
        You may say you are unsure.
        """
    else:
        early_game = ""

    prompt = f"""
        You are NOT an AI assistant. You are a PLAYER in a Mafia social deduction game.
        your name is: {name}
        your role is: {role}
        you have this personality: {personality}

        Game memory: {memory_summary}

        {early_game}

        The rules you can optionally follow are:
        - You are playing to win
        - Don't admit your true role.
        - Answer maximally with 3 sentences.
        - Speak naturally.
        - Voting "None" is acceptable if you have no suspicion.
        - If you vote None too often, civilians may lose.

        When suspecting someone, you MUST refer to:
        - What they voted
        - Who they accused
        - Contradictions in statements
        - Changes in opinion between days

        {extra}

        Alive players: {alive_players}

        Situation: {situation}
    """

    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content.strip()


while not game_over:
    # noc - killer vybira koho vyradi
    log(f"\nNIGHT {number_of_days}")
    # najde z pole "alive" kdo je killer a victims - da do variable
    killer = [p for p in alive if players[p]["role"] == "killer"][0]
    victims = [p for p in alive if p != killer]

    reply = ask_ai(killer, f"It is Night {number_of_days}. Choose ONE player to kill from this list: {victims}. Answer with ONE name only")
    victim = reply.strip()

    if victim in victims:
        alive.remove(victim)
        log(f"{victim} was killed during the night.")
    else:
        log("The killer failed to kill anyone. Noone died tonight.")
        victim = None

    if killer not in alive:
        log(f"\n Civilians WIN! The killer was {killer}")
        break
    if len(alive) == 2 and killer in alive:
        log(f"\nKiller WINS! The killer was {killer}")
        break

    # den - verejna debata
    log("\nDAY - DISCUSSION")

    statements = {}

    if victim:
        day_info = f"Last night {victim} died"
    else:
        day_info = "No one died last night."

    for name in alive:
        reply = ask_ai(name, f"It is Day {number_of_days}. {day_info}. Who do you suspect and why?")
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
    # NOONE VOTED
    if not votes:
        log("\nNo votes were cast. No one was voted out today.")
        vote_out = None
    else:
        max_votes = max(votes.values())
        candidates = [p for p, v in votes.items() if v == max_votes]

        if len(candidates) > 1:
            log("\nVoting ended in a tie. No one was voted out today.")
            vote_out = None
        else:
            vote_out = candidates[0]
            alive.remove(vote_out)
            log(f"\n{vote_out} was voted out.")
            log(f"His/Her role was: {players[vote_out]['role']}")

    if vote_out == killer:
        log(f"\nCivilians WIN! The killer was VOTED OUT")
        break
    if len(alive) == 2 and killer in alive:
        log("\nKILLER WINS! Only one civilian remains.")
        break
    
    day_record = {
    "day": number_of_days,
    "discussion": statements,
    "votes": votes,
    "lynched": vote_out
}
    memory["days"].append(day_record)

    number_of_days += 1
