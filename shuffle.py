import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Tuple
import random


class Player:
    def __init__(self, name: str, seed: int):
        self.name = name
        self.seed = seed
        self.points = 0
        self.game_count = 0
        self.previous_partners = set()
        self.bye_count = 0

class Team:
    def __init__(self, player1: Player, player2: Player, is_bye=False):
        self.players = [player1, player2]
        self.points = 0
        self.game_count = 0

class Tournament:
    def __init__(self, players: List[Player], num_rounds: int, first_to: int):
        self.players = players
        self.num_rounds = num_rounds
        self.teams: List[Team] = []
        self.matches: List[Tuple[Team, Team]] = []
        self.current_round = 0
        self.bye_players: List[Player] = []
        self.first_to = first_to

    def create_new_teams(self):
        # Sort players by bye_count (ascending), then points (descending), 
        # then game_count (descending), and finally by seed
        sorted_players = sorted(self.players, key=lambda x: (-x.points, -x.game_count, x.seed))
        
        # Bye assignment
        bye_players = []
        number_of_bye_players = len(sorted_players) % 4
        if number_of_bye_players != 0:
            for i in range(number_of_bye_players):
                min_byes = min(player.bye_count for player in self.players)
                players_with_least_byes = [player for player in self.players if player.bye_count == min_byes]
                random_player_index = random.randint(0, len(players_with_least_byes) - 1)
                bye_player = players_with_least_byes.pop(random_player_index)
                bye_player.bye_count += 1
                bye_players.append(bye_player)
                sorted_players.remove(bye_player)
                self.bye_players = bye_players
        else:
            self.bye_players = []

        # Now create teams with remaining players
        self.teams = []
    
        while len(sorted_players) > 0:
            top_player = sorted_players[0]
            best_partner = None
            best_partner_index = -1

            # Try to find a partner that hasn't been paired with top_player before
            for player in sorted_players[::-1]:
                if player.name not in top_player.previous_partners and player.name != top_player.name:
                    best_partner = player
                    best_partner_index = sorted_players.index(player)
                    break

            # If no new partner found, pair with the lowest ranked available player
            if best_partner is None:
                best_partner = sorted_players[-1]
                best_partner_index = -1

            # Create the team and update previous partners
            self.teams.append(Team(top_player, best_partner))
            top_player.previous_partners.add(best_partner.name)
            best_partner.previous_partners.add(top_player.name)

            # Remove the paired players from the list
            sorted_players.pop(best_partner_index)
            sorted_players.pop(0)


    def create_matches(self):
        self.matches = []
        # Sort teams based on average player points, game count, and seed
        sorted_teams = sorted(self.teams, key=lambda x: (
            -sum(p.points for p in x.players if p) / len([p for p in x.players if p]),
            -sum(p.game_count for p in x.players if p) / len([p for p in x.players if p]),
            min(p.seed for p in x.players if p)
        ))

        while len(sorted_teams) >= 2:
            team1 = sorted_teams.pop(0)
            team2 = sorted_teams.pop(0)
            self.matches.append((team1, team2))

    def update_results(self, results: List[Tuple[int, int]]):
        for (team1, team2), (score1, score2) in zip(self.matches, results):
            if score1 > score2:
                winner, loser = team1, team2
            else:
                winner, loser = team2, team1

            winner.points += 1
            winner.game_count += max(score1, score2)
            for player in winner.players:
                if player:
                    player.points += 1
                    player.game_count += max(score1, score2)

            if loser:
                loser.game_count += min(score1, score2)
                for player in loser.players:
                    if player:
                        player.game_count += min(score1, score2)

            # Update previous partners
            for p1 in team1.players:
                for p2 in team2.players if team2 else []:
                    if p1 and p2:
                        p1.previous_partners.add(p2.name)
                        p2.previous_partners.add(p1.name)
        
        # update bye players
        for bye_player in self.bye_players:
            bye_player.points += 1
            bye_player.game_count += self.first_to

    def get_standings(self):
        return sorted(self.players, key=lambda x: (-x.points, -x.game_count, x.seed))

    def get_grand_finals_participants(self):
        return self.get_standings()[:4]

class TournamentGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Milly Shuffle")
        self.master.geometry("600x400")
        self.tournament = None
        self.create_input_screen()

    def create_input_screen(self):
        self.clear_screen()
        
        ttk.Label(self.master, text="Enter players (one per line, in seed order):").pack(pady=10)
        self.players_text = tk.Text(self.master, height=10, width=50)
        self.players_text.pack(pady=10)
        
        ttk.Label(self.master, text="Number of rounds:").pack()
        self.rounds_entry = ttk.Entry(self.master)
        self.rounds_entry.pack(pady=10)

        ttk.Label(self.master, text="Best of:").pack()
        self.best_of_entry = ttk.Entry(self.master)
        self.best_of_entry.pack(pady=10)
        
        ttk.Button(self.master, text="Start Tournament", command=self.start_tournament).pack(pady=20)

    def start_tournament(self):
        players_input = self.players_text.get("1.0", tk.END).strip().split("\n")
        num_rounds = int(self.rounds_entry.get())
        best_of = int(self.best_of_entry.get()) // 2 + 1
        
        if len(players_input) % 2 != 0:
            messagebox.showerror("Error", "Number of players must be even.")
            return
        
        players = [Player(name, i+1) for i, name in enumerate(players_input)]
        self.tournament = Tournament(players, num_rounds, best_of)
        self.tournament.create_new_teams()
        self.show_matches()

    def show_matches(self):
        self.clear_screen()
        self.tournament.create_matches()
        
        ttk.Label(self.master, text=f"Round {self.tournament.current_round + 1}").pack(pady=10)
        
        self.match_frames = []
        for i, (team1, team2) in enumerate(self.tournament.matches):
            frame = ttk.Frame(self.master)
            frame.pack(pady=5)
            
            ttk.Label(frame, text=f"{team1.players[0].name}/{team1.players[1].name} vs {team2.players[0].name}/{team2.players[1].name}").pack(side=tk.LEFT)
            team1_score = ttk.Entry(frame, width=3)
            team1_score.pack(side=tk.LEFT, padx=5)
            team2_score = ttk.Entry(frame, width=3)
            team2_score.pack(side=tk.LEFT)
            
            self.match_frames.append((team1_score, team2_score))
        
        for bye_player in self.tournament.bye_players:
            frame = ttk.Frame(self.master)
            frame.pack(pady=5)
            ttk.Label(frame, text=f"bye: {bye_player.name}").pack(side=tk.LEFT)
        
        ttk.Button(self.master, text="Submit Results", command=self.submit_results).pack(pady=20)

    def submit_results(self):
        results = []
        for team1_score, team2_score in self.match_frames:
            score1 = int(team1_score.get()) if team1_score else 2
            score2 = int(team2_score.get()) if team2_score else 0
            results.append((score1, score2))
        
        self.tournament.update_results(results)
        self.tournament.current_round += 1
        
        if self.tournament.current_round < self.tournament.num_rounds:
            self.tournament.create_new_teams()
            self.show_matches()
        else:
            self.show_grand_finals()

    def show_grand_finals(self):
        self.clear_screen()
        
        ttk.Label(self.master, text="Grand Finals Participants", font=("Arial", 16, "bold")).pack(pady=20)
        
        participants = self.tournament.get_grand_finals_participants()
        for i, player in enumerate(participants, 1):
            ttk.Label(self.master, text=f"{i}. {player.name} - Points: {player.points}, Game Count: {player.game_count}").pack(pady=5)
        
        ttk.Button(self.master, text="Show Final Standings", command=self.show_final_standings).pack(pady=5)
        ttk.Button(self.master, text="New Tournament", command=self.create_input_screen).pack(pady=5)

    def show_final_standings(self):
        self.clear_screen()
        
        ttk.Label(self.master, text="Final Standings", font=("Arial", 16, "bold")).pack(pady=20)
        
        # Create a frame for the standings
        standings_frame = ttk.Frame(self.master)
        standings_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Create a canvas and scrollbar
        canvas = tk.Canvas(standings_frame)
        scrollbar = ttk.Scrollbar(standings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add column headers
        ttk.Label(scrollable_frame, text="Rank", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(scrollable_frame, text="Player", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(scrollable_frame, text="Points", font=("Arial", 12, "bold")).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(scrollable_frame, text="Game Count", font=("Arial", 12, "bold")).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(scrollable_frame, text="Byes", font=("Arial", 12, "bold")).grid(row=0, column=4, padx=5, pady=5)

        # Add player data
        standings = self.tournament.get_standings()
        for i, player in enumerate(standings, 1):
            ttk.Label(scrollable_frame, text=f"{i}").grid(row=i, column=0, padx=5, pady=2)
            ttk.Label(scrollable_frame, text=f"{player.name}").grid(row=i, column=1, padx=5, pady=2)
            ttk.Label(scrollable_frame, text=f"{player.points}").grid(row=i, column=2, padx=5, pady=2)
            ttk.Label(scrollable_frame, text=f"{player.game_count}").grid(row=i, column=3, padx=5, pady=2)
            ttk.Label(scrollable_frame, text=f"{player.bye_count}").grid(row=i, column=4, padx=5, pady=2)

        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(self.master, text="Show Grand Finals", command=self.show_grand_finals).pack(pady=5)
        ttk.Button(self.master, text="New Tournament", command=self.create_input_screen).pack(pady=5)

    def clear_screen(self):
        for widget in self.master.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TournamentGUI(root)
    root.mainloop()